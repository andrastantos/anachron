#!/usr/bin/python3
from math import *

uart1_clock_rate = 50_000_000

def calc_settings(baud_rate):
    prescaler = int(log2((uart1_clock_rate // baud_rate) >> 8)+1)
    divider = int(uart1_clock_rate / (1 << prescaler) / baud_rate / 2 + 0.5)
    actual_baud_rate = uart1_clock_rate // (1 << prescaler) // divider // 2
    error = actual_baud_rate / baud_rate - 1
    print(f"ideal baud rate: {baud_rate}, prescaler: {prescaler} ({1<<prescaler}), divider: {divider}, actual baud rate: {actual_baud_rate} error: {error*100:0.2f}%")

for b in (4800, 9600, 19200, 57600, 115200):
    calc_settings(b)
