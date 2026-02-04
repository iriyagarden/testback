"""
并发运行购物车测试
"""
import subprocess
import multiprocessing
import time
from datetime import datetime
import sys
import os
import json

def run_test(test_module, browser="chrome"):
    """运行单个测试模块，增加异常捕获和耗时统计"""
    start_time = time.time()
    cmd = [
        sys.executable, '-m', 'pytest',
        test_module,
        f"--browser={browser}",
        f"--html=reports/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
        "-v"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        status = "✓ 通过" if result.returncode == 0 else "✗ 失败"
        error = None
    except Exception as e:
        result = None
        status = "✗ 异常"
        error = str(e)
    end_time = time.time()
    return {
        "module": test_module,
        "returncode": result.returncode if result else -1,
        "stdout": result.stdout if result else '',
        "status": status,
        "error": error,
        "duration": round(end_time - start_time, 2)
    }

if __name__ == "__main__":
    test_modules = [
        "shopping_cart_test.py::TestShoppingCart",
        "shopping_cart_test.py::TestDataDrivenShoppingCart"
    ]
    print("并发执行测试用例...\n")
    with multiprocessing.Pool(processes=2) as pool:
        results = pool.map(run_test, test_modules)
    print("\n" + "="*50)
    print("测试执行完成")
    print("="*50)
    for result in results:
        print(f"{result['module']}: {result['status']}  用时: {result['duration']}s")
        if result['error']:
            print(f"  错误: {result['error']}")

    # 保存测试结果到桌面
    save_result_to_desktop(results, "test_results.txt")

def save_result_to_desktop(content, filename=None, append=False):
    """
    将运行结果保存到桌面，支持字符串、字典、列表等多种类型
    
    参数:
        content: 要保存的内容（字符串、字典、列表等）
        filename: 文件名（可选，默认使用时间戳）
        append: 是否追加模式（默认False，覆盖模式）
    
    返回:
        保存的文件路径，如果失败返回None
    """
    # 获取桌面路径
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    
    # 如果没有指定文件名，使用时间戳
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"result_{timestamp}.txt"
    
    # 确保文件名有.txt扩展名
    if not filename.endswith('.txt'):
        filename += '.txt'
    
    # 完整的文件路径
    file_path = os.path.join(desktop_path, filename)
    
    # 将内容转换为字符串
    if isinstance(content, (dict, list)):
        text_content = json.dumps(content, indent=2, ensure_ascii=False)
    else:
        text_content = str(content)
    
    # 写入文件
    try:
        mode = 'a' if append else 'w'
        with open(file_path, mode, encoding='utf-8') as f:
            if append:
                f.write('\n' + '='*50 + '\n')
                f.write(f"追加时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write('='*50 + '\n')
            f.write(text_content)
            if not text_content.endswith('\n'):
                f.write('\n')
        print(f"结果已保存到: {file_path}")
        return file_path
    except Exception as e:
        print(f"保存文件时出错: {e}")
        return None