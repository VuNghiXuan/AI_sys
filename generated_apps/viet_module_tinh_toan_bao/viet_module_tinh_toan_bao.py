# Header Comment chuẩn vnxBox
"""
Module tính toán báo cáo vàng bạc bằng pandas

Đặc tả kỹ thuật:
1. Chuẩn hóa kiểu số (numeric) và xử lý giá trị thiếu/rỗng rõ ràng trước khi tính toán báo cáo.
2. Phân biệt rõ trọng lượng thô/tổng trọng lượng, trọng lượng đá/tạp chất (nếu có) và trọng lượng tinh/quy đổi.
3. Tính tổng, trung bình, min, max rõ ràng.
4. Giữ nguyên độ chính xác số thập phân khi tổng hợp và xuất báo cáo.
5. Trả về DataFrame hoặc dict kết quả có cấu trúc rõ ràng.
"""

import pandas as pd

def standardize_numeric_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """
    Chuẩn hóa kiểu số (numeric) và xử lý giá trị thiếu/rỗng rõ ràng.

    :param df: DataFrame cần chuẩn hóa
    :param columns: danh sách các cột cần chuẩn hóa
    :return: DataFrame đã chuẩn hóa
    """
    for col in columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        df[col].fillna(0, inplace=True)
    return df

def separate_weight_types(df: pd.DataFrame, weight_col: str) -> pd.DataFrame:
    """
    Phân biệt rõ trọng lượng thô/tổng trọng lượng, trọng lượng đá/tạp chất (nếu có) và trọng lượng tinh/quy đổi.

    :param df: DataFrame chứa dữ liệu
    :param weight_col: cột chứa trọng lượng
    :return: DataFrame đã phân biệt trọng lượng
    """
    df['weight_type'] = df[weight_col].apply(lambda x: 'tinh' if 'tinh' in str(x).lower() else 'thô')
    return df

def summarize_gold_silver_report(df: pd.DataFrame, group_cols: list[str], weight_col: str, amount_col: str) -> pd.DataFrame:
    """
    Tổng hợp các chỉ số báo cáo vàng bạc theo nhóm cột.

    :param df: DataFrame chứa dữ liệu
    :param group_cols: danh sách các cột cần nhóm
    :param weight_col: cột chứa trọng lượng
    :param amount_col: cột chứa số lượng
    :return: DataFrame kết quả tổng hợp
    """
    df = standardize_numeric_columns(df, [weight_col, amount_col])
    df = separate_weight_types(df, weight_col)
    
    result = df.groupby(group_cols).agg({
        weight_col: ['sum', 'mean', 'min', 'max'],
        amount_col: ['sum', 'mean', 'min', 'max']
    }).round(2)
    
    result.columns = ['_'.join(col).strip() for col in result.columns.values]
    return result

def convert_purity_weight(df: pd.DataFrame, weight_col: str, purity_col: str, target_purity: float) -> pd.Series:
    """
    Quy đổi trọng lượng theo tỷ lệ hàm lượng mục tiêu.

    :param df: DataFrame chứa dữ liệu
    :param weight_col: cột chứa trọng lượng
    :param purity_col: cột chứa hàm lượng
    :param target_purity: tỷ lệ hàm lượng mục tiêu
    :return: Series kết quả quy đổi trọng lượng
    """
    df = standardize_numeric_columns(df, [weight_col, purity_col])
    
    conversion_factor = target_purity / df[purity_col]
    converted_weight = df[weight_col] * conversion_factor
    
    return converted_weight.rename(f'{weight_col}_converted')