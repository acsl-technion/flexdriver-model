#!/usr/bin/env python

'''Performance model for FlexDriver.'''

import numpy as np
import pandas as pd

__author__ = 'Haggai Eran'
__copyright__ = 'Copyright 2021, Haggai Eran'
__license__ = 'BSD-2-Clause'

# Model parameters

pci_mtu = 256 # byte
pci_max_read_req = 512 # byte
pci_tlp_header_size = 24 # byte
pci_read_completion_header_size = 20 # byte
pci_single_lane_rate = 8  # Gbps - Gen. 3
pci_utilization = 0.95

default_packet_size = np.arange(4, 9001, 4)

def port_packet_rate(df, packet_size, linerate):
    '''Packet rate in Mpps'''
    df['size'] = packet_size
    df['ethernet_packet_rate'] = linerate * 1e3 / 8 / (np.maximum(packet_size, 64) + 20)

def segmentation_overhead(packet_size, mtu, header_size):
    return np.floor_divide(packet_size, mtu) * (mtu + header_size) + np.where(packet_size % mtu > 0, (packet_size % mtu) + header_size, 0)

def data_overheads(df):
    df['inbound_rx_data'] = segmentation_overhead(df['size'], pci_mtu, pci_tlp_header_size)
    df['outbound_tx_data'] = segmentation_overhead(df['size'], pci_mtu, pci_read_completion_header_size)

sx_cqe_moderation = 16
cqe_size = 64 # byte

def inbound_control_overhead(df, blueflame_always_on):
    '''Compute the overhead for inbound traffic in bytes.'''
    sx_wqe_read = pci_tlp_header_size if blueflame_always_on else 0
    sx_cqe_write = (cqe_size + pci_tlp_header_size) / sx_cqe_moderation
    sx_data_read_req = np.ceil(df['size'] / pci_max_read_req) * pci_tlp_header_size
    rx_cqe_write = cqe_size + pci_tlp_header_size
    df['pci_inbound_control_overhead'] = sx_wqe_read + sx_cqe_write + sx_data_read_req + rx_cqe_write

wqe_size = 48 # byte
bf_wqe_size = 64 # byte

def outbound_control_overhead(df, blueflame_always_on=False):
    '''Compute the overhead for outbound traffic in bytes.'''
    if blueflame_always_on:
        sx_wqe_outbound = bf_wqe_size + pci_tlp_header_size # write
    else:
        sx_wqe_outbound = wqe_size + np.ceil(pci_read_completion_header_size / (pci_mtu / wqe_size)) # read completion
    df['pci_outbound_control_overhead'] = sx_wqe_outbound

def pci_overheads(df, pci_lanes, blueflame_always_on):
    '''Compute PCIe overheads.'''
    inbound_control_overhead(df, blueflame_always_on=blueflame_always_on)
    outbound_control_overhead(df, blueflame_always_on=blueflame_always_on)

    pci_linerate = pci_lanes * pci_single_lane_rate * pci_utilization - 1  # Gbps

    dirs = ('inbound', 'outbound')
    data = ('inbound_rx_data', 'outbound_tx_data')

    for dir, data_col in zip(dirs, data):
        df[f'pci_{dir}_all'] = df[data_col] + df[f'pci_{dir}_control_overhead']
        df[f'pci_packet_rate_{dir}'] = pci_linerate / df[f'pci_{dir}_all'] / 8 * 1000  # Mpps

    df['pci_packet_rate'] = np.minimum(*(df[f'pci_packet_rate_{dir}'] for dir in dirs))
    df['pci_expected_bandwidth'] = df['pci_packet_rate'] * df['size'] * 8 / 1000 # Gbps

def fld_model(linerate=50, packet_size=default_packet_size, pci_lanes=8, blueflame_always_on=True, interface='remote', **kwargs):
    '''Compute the expected throughput for the given parameters and packet sizes.
    
    linerate -- Ethernet line-rate in Gbps.
    packet_size -- an array of packet sizes to calculate for.
    pci_lanes -- number of PCIe lanes.
    blueflame_always_on -- whether or not the FLD IP uses BlueFlame for tx descriptors.
    interface -- "remote" or "local".

    Returns a dataframe with the results along with the kwargs assigned.
    '''
    df = pd.DataFrame()
    port_packet_rate(df, packet_size, linerate)
    data_overheads(df)
    pci_overheads(df, pci_lanes, blueflame_always_on=blueflame_always_on)
    df['ethernet_linerate'] = df['ethernet_packet_rate'] * df['size'] * 8 / 1000
    df['bandwidth'] = df['pci_expected_bandwidth']
    if interface == 'remote':
        df['bandwidth'] = np.minimum(
            df['bandwidth'],
            df['ethernet_linerate']
        )
    else:
        assert interface == 'local'
    df['linerate'] = linerate
    df = df.assign(interface=interface, **kwargs)
    return df
