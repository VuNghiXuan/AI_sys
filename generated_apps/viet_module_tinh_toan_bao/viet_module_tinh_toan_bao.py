# Author: Coder Agent
# Date: [Ngày hiện tại]
# Description: Module tính toán báo cáo vàng bạc bằng pandas
# Version: 1.0

import pandas as pd
import numpy as np
import logging

# Configuring logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def read_data(file_path):
    """
    Đọc dữ liệu từ file CSV hoặc Excel.
    
    :param file_path: Đường dẫn đến file CSV hoặc Excel
    :return: DataFrame chứa dữ liệu
    """
    try:
        if file_path.endswith('.csv'):
            data = pd.read_csv(file_path)
        elif file_path.endswith('.xlsx'):
            data = pd.read_excel(file_path)
        else:
            raise ValueError("Định dạng file không hỗ trợ")
        return data
    except Exception as e:
        logging.error(f"Lỗi khi đọc file: {e}")
        raise

def calculate_statistics(data):
    """
    Tính toán các chỉ số và thông số cần thiết cho báo cáo vàng bạc.
    
    :param data: DataFrame chứa dữ liệu
    :return: Dictionary chứa các chỉ số và thông số
    """
    try:
        statistics = {
            'Giá trị trung bình': data.mean(),
            'Giá trị tối đa': data.max(),
            'Giá trị tối thiểu': data.min(),
            'Phân phối dữ liệu': data.describe()
        }
        return statistics
    except Exception as e:
        logging.error(f"Lỗi khi tính toán thống kê: {e}")
        raise

def save_report(statistics, output_path):
    """
    Xuất báo cáo dưới dạng file CSV hoặc Excel.
    
    :param statistics: Dictionary chứa các chỉ số và thông số
    :param output_path: Đường dẫn đến file xuất báo cáo
    """
    try:
        if output_path.endswith('.csv'):
            pd.DataFrame(statistics).to_csv(output_path, index=False)
        elif output_path.endswith('.xlsx'):
            pd.DataFrame(statistics).to_excel(output_path, index=False)
        else:
            raise ValueError("Định dạng file không hỗ trợ")
        logging.info(f"Báo cáo đã được lưu tại {output_path}")
    except Exception as e:
        logging.error(f"Lỗi khi lưu báo cáo: {e}")
        raise

def main(file_path, output_path):
    """
    Hàm chính để thực hiện tính toán báo cáo vàng bạc.
    
    :param file_path: Đường dẫn đến file CSV hoặc Excel
    :param output_path: Đường dẫn đến file xuất báo cáo
    """
    try:
        data = read_data(file_path)
        statistics = calculate_statistics(data)
        save_report(statistics, output_path)
        logging.info("Tính toán báo cáo vàng bạc hoàn tất")
    except Exception as e:
        logging.error(f"Lỗi chung: {e}")
        raise

if __name__ == "__main__":
    file_path = 'data.csv'  # Đường dẫn đến file CSV hoặc Excel
    output_path = 'report.csv'  # Đường dẫn đến file xuất báo cáo
    main(file_path, output_path)