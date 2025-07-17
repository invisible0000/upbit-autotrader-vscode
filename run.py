#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
업비트 자동매매 시스템 실행 스크립트

이 스크립트는 업비트 자동매매 시스템을 실행하는 진입점입니다.
"""

import sys
from upbit_auto_trading.__main__ import main

if __name__ == "__main__":
    sys.exit(main())