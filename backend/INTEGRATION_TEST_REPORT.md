# 四大模块集成测试执行报告

## 执行环境
- Python 版本: 3.14.0
- pytest 版本: 8.4.1
- 执行时间: 2025-11-14 19:08:47
- 执行系统: Windows PowerShell

## 测试结果汇总

### Library Module
- Domain Tests: 8 PASSED | 6 FAILED | 0 ERRORS (0.07s)
- Repository Tests: 0 PASSED | 11 FAILED | 0 ERRORS
- Application Tests: 0 PASSED | 12 FAILED | 10 ERRORS
- **小计**: 8 PASSED | 29 FAILED | 10 ERRORS

### Bookshelf Module

- Domain Tests: 2 PASSED | 8 FAILED | 0 ERRORS
- Repository Tests: 0 PASSED | 8 FAILED | 0 ERRORS
- Application Tests: 0 PASSED | 0 FAILED | 18 ERRORS
- **小计**: 2 PASSED | 16 FAILED | 18 ERRORS

### Book Module

- Domain Tests: 21 PASSED | 0 FAILED | 0 ERRORS (0.07s)
- Repository Tests: 12 PASSED | 0 FAILED | 0 ERRORS (0.09s)
- Application Tests: 0 PASSED | 27 FAILED | 0 ERRORS (0.29s)
- Infrastructure Tests: 0 PASSED | 3 FAILED | 0 ERRORS (26 SKIPPED)
- **小计**: 33 PASSED | 30 FAILED | 0 ERRORS

### Block Module

- Domain Tests: COLLECTION ERROR | 0 PASSED | 0 FAILED
- Repository Tests: COLLECTION ERROR | 0 PASSED | 0 FAILED
- Paperballs Recovery Tests: SYNTAX ERROR | 0 PASSED | 0 FAILED
- **小计**: 0 PASSED | 0 FAILED | 3 COLLECTION ERRORS

## 总体汇总

总计: 43 PASSED | 75 FAILED | 31 ERRORS
通过率: 28.9%
总测试数: 149
执行总时间: ~1.5s (估计)
