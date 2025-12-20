import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
import platform

# 忽略警告訊息，保持介面乾淨
warnings.filterwarnings('ignore')

# --- 設定中文字型 (避免繪圖時出現亂碼) ---
def set_chinese_font():
    system_name = platform.system()
    if system_name == "Windows":
        plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei'] # 微軟正黑體
    elif system_name == "Darwin": # Mac
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
    else:
        plt.rcParams['font.sans-serif'] = ['SimHei'] # Linux/Colab 常用
    plt.rcParams['axes.unicode_minus'] = False

set_chinese_font()

# 1. 資料讀取與預處理
print("🔄 正在讀取 HR 員工離職資料...")

# 這裡使用你上傳的檔案名稱
file_name = 'HR-Employee-Attrition-完美中文版.xlsx - 工作表 1 - HR-Employee-Attrition-完.csv'

try:
    df = pd.read_csv(file_name)
    print(f"✅ 成功讀取！資料大小：{df.shape[0]} 筆員工資料，{df.shape[1]} 個欄位")
except FileNotFoundError:
    print(f"❌ 找不到檔案：{file_name}")
    print("請確認檔案是否與程式在同一個資料夾內。")
    exit()

# 預處理：將 '流失' 轉換為數值方便計算 (是=1, 否=0)
df['流失數值'] = df['流失'].apply(lambda x: 1 if x == '是' else 0)

# 2. 互動式篩選分析 (基礎功能)
def interactive_filter():
    print("\n" + "="*60)
    print("🎯 1. 員工離職互動篩選器")
    print("="*60)
    
    print("💡 提示：輸入條件來觀察特定族群的離職率")
    dept_input = input("請輸入部門關鍵字 (如：研發, 銷售，空白則選全部)：").strip()
    overtime_input = input("是否加班 (是/否，空白則選全部)：").strip()
    
    filtered_df = df.copy()
    
    if dept_input:
        filtered_df = filtered_df[filtered_df['部門'].str.contains(dept_input, na=False)]
    if overtime_input in ['是', '否']:
        filtered_df = filtered_df[filtered_df['加班'] == overtime_input]
        
    total = len(filtered_df)
    left_count = len(filtered_df[filtered_df['流失'] == '是'])
    rate = (left_count / total * 100) if total > 0 else 0
    
    print(f"\n📊 篩選結果：")
    print(f"   符合條件人數：{total} 人")
    print(f"   離職人數：{left_count} 人")
    print(f"   ⚠️ 該族群離職率：{rate:.2f}% (全體平均約 {(df['流失']=='是').mean()*100:.1f}%)")

# 3. 關鍵類別因子分析 (探討原因用)
def category_analysis():
    print("\n" + "="*60)
    print("🧐 2. 離職關鍵因子分析 (類別型)")
    print("="*60)
    print("此功能幫助我們找出「哪種特徵的員工」容易離職。\n")
    
    factors = {
        '1': '出差頻率',
        '2': '加班',
        '3': '婚姻狀態',
        '4': '教育領域',
        '5': '工作滿意度' # 雖然是數字，但通常視為類別等級
    }
    
    print("請選擇要分析的因子：")
    for k, v in factors.items():
        print(f"{k}. {v}")
        
    choice = input("輸入選項 (1-5)：").strip()
    col = factors.get(choice)
    
    if col:
        # 計算各組的離職率
        group_stats = df.groupby(col)['流失數值'].mean() * 100
        group_counts = df[col].value_counts()
        
        result = pd.DataFrame({'人數': group_counts, '離職率(%)': group_stats})
        print(f"\n📊 【{col}】與離職率的關係：")
        print(result.sort_values('離職率(%)', ascending=False))
        
        # 繪圖
        plt.figure(figsize=(10, 5))
        sns.barplot(x=result.index, y=result['離職率(%)'], palette='Reds_d')
        plt.title(f'{col} - 離職率分析', fontsize=14)
        plt.ylabel('離職率 (%)')
        plt.axhline(y=df['流失數值'].mean()*100, color='blue', linestyle='--', label='全公司平均')
        plt.legend()
        plt.show()
    else:
        print("無效選項。")

# 4. 薪資與年資比較 (數值型分析)
def numerical_comparison():
    print("\n" + "="*60)
    print("💰 3. 薪資與年資深度比較")
    print("="*60)
    print("比較「離職者」與「在職者」的平均數據差異。\n")
    
    cols_to_compare = ['月薪', '年齡', '總工作年資', '在公司年資', '上次升遷年資']
    
    comparison = df.groupby('流失')[cols_to_compare].mean().round(1)
    print(comparison.T) # 轉置表格比較好閱讀
    
    print("\n📈 正在繪製薪資分佈圖...")
    plt.figure(figsize=(10, 6))
    sns.boxplot(x='流失', y='月薪', data=df, palette='Set2')
    plt.title('離職者 vs 在職者：月薪分佈比較')
    plt.show()
    
    print("\n💡 觀察重點：如果離職者的箱型圖(Boxplot)位置明顯較低，代表低薪可能是離職主因。")

# 5. 主程式選單
if __name__ == "__main__":
    while True:
        print("\n" + "█"*30)
        print(" 🚀 HR 員工離職數據探勘系統")
        print("█"*30)
        print("1. 互動篩選 (查詢特定族群)")
        print("2. 因子分析 (加班、出差、滿意度對離職的影響)")
        print("3. 數值比較 (薪水、年資是否有差異)")
        print("4. 顯示資料欄位定義")
        print("0. 離開系統")
        
        ans = input("\n請選擇功能 (0-4)：").strip()
        
        if ans == '1':
            interactive_filter()
        elif ans == '2':
            category_analysis()
        elif ans == '3':
            numerical_comparison()
        elif ans == '4':
            print(f"\n📋 資料欄位：{list(df.columns)}")
        elif ans == '0':
            print("👋 分析結束，祝報告順利！")
            break
        else:
            print("❌ 輸入錯誤，請重試。")
