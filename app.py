import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 1. 讀取你的Excel檔案
print("🔄 正在讀取HR員工離職資料...")
df = pd.read_excel('HR-Employee-Attrition-Wan-Mei-Zhong-Wen-Ban.xlsx')

print(f"📊 資料總覽：{df.shape[0]}筆員工資料，{df.shape[1]}個欄位")
print("\n前5筆資料預覽：")
print(df.head())

# 2. 互動式篩選分析函數
def 離職分析篩選():
    print("\n" + "="*60)
    print("🎯 員工離職互動分析系統")
    print("="*60)
    
    # 顯示可用篩選條件
    print("\n📋 可篩選條件：")
    print("- 性別：男/女")
    print("- 年齡範圍：輸入最小年齡,最大年齡 (例如: 25,45)")
    print("- 部門：輸入部門名稱")
    print("- 離職狀態：是/否")
    
    # 互動輸入
    性別 = input("\n請輸入性別 (男/女/全部)：").strip()
    年齡_min = input("請輸入最小年齡 (0表示不篩選)：").strip()
    年齡_max = input("請輸入最大年齡 (0表示不篩選)：").strip()
    部門 = input("請輸入部門 (空白表示全部)：").strip()
    離職狀態 = input("篩選離職員工？(是/否/全部)：").strip()
    
    # 建立篩選條件
    filtered_df = df.copy()
    
    if 性別 != '全部' and 性別 in ['男', '女']:
        filtered_df = filtered_df[filtered_df['性別'] == 性別]
    
    if 年齡_min != '0':
        filtered_df = filtered_df[filtered_df['年齡'] >= int(年齡_min)]
    if 年齡_max != '0':
        filtered_df = filtered_df[filtered_df['年齡'] <= int(年齡_max)]
    
    if 部門:
        filtered_df = filtered_df[filtered_df['部門'].str.contains(部門, na=False)]
    
    if 離職狀態 != '全部':
        if 離職狀態 == '是':
            filtered_df = filtered_df[filtered_df['離職'] == '是']
        elif 離職狀態 == '否':
            filtered_df = filtered_df[filtered_df['離職'] == '否']
    
    # 分析結果
    總人數 = len(filtered_df)
    離職人數 = len(filtered_df[filtered_df['離職'] == '是'])
    離職率 = (離職人數 / 總人數 * 100) if 總人數 > 0 else 0
    
    print("\n📈 篩選結果摘要：")
    print(f"   總人數：{總人數:>4}")
    print(f"   離職人數：{離職人數:>4}")
    print(f"   離職率：{離職率:.1f}%")
    
    if 總人數 > 0:
        print("\n👥 各部門離職情況：")
        dept_summary = filtered_df.groupby('部門')['離職'].apply(lambda x: (x == '是').sum()).sort_values(ascending=False)
        for dept, count in dept_summary.items():
            dept_total = len(filtered_df[filtered_df['部門'] == dept])
            dept_rate = (count / dept_total * 100) if dept_total > 0 else 0
            print(f"   {dept:<15}：{count:>3}人 ({dept_rate:>5.1f}%)")
    
    return filtered_df

# 3. 年齡分組分析
def 年齡分組分析():
    print("\n" + "="*50)
    print("📊 年齡分組離職分析")
    print("="*50)
    
    df['年齡組'] = pd.cut(df['年齡'], bins=[0, 25, 35, 45, 55, 100], 
                          labels=['<25', '25-34', '35-44', '45-54', '55+'])
    
    age_analysis = df.groupby('年齡組').agg({
        '離職': lambda x: (x == '是').sum(),
        '員工ID': 'count'
    }).rename(columns={'離職': '離職人數', '員工ID': '總人數'})
    
    age_analysis['離職率'] = (age_analysis['離職人數'] / age_analysis['總人數'] * 100).round(1)
    print(age_analysis)
    
    # 繪製年齡離職率圖
    plt.figure(figsize=(10, 6))
    plt.bar(age_analysis.index, age_analysis['離職率'], color='salmon', alpha=0.7)
    plt.title('各年齡組離職率比較', fontsize=16, pad=20)
    plt.ylabel('離職率 (%)')
    plt.xlabel('年齡組')
    plt.grid(axis='y', alpha=0.3)
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.show()

# 4. 性別與部門交叉分析
def 性別部門分析():
    print("\n" + "="*50)
    print("👩‍💼👨‍💼 性別×部門離職分析")
    print("="*50)
    
    cross_analysis = df.groupby(['性別', '部門']).agg({
        '離職': lambda x: (x == '是').sum(),
        '員工ID': 'count'
    }).rename(columns={'離職': '離職人數', '員工ID': '總人數'})
    
    cross_analysis['離職率'] = (cross_analysis['離職人數'] / cross_analysis['總人數'] * 100).round(1)
    print(cross_analysis)
    
    # 熱力圖
    pivot_table = df.pivot_table(index='性別', columns='部門', 
                               values='離職', aggfunc=lambda x: (x == '是').mean()*100)
    plt.figure(figsize=(12, 6))
    sns.heatmap(pivot_table, annot=True, fmt='.1f', cmap='YlOrRd', cbar_kws={'label': '離職率 (%)'})
    plt.title('性別×部門離職率熱力圖')
    plt.tight_layout()
    plt.show()

# 5. 主要程式執行
if __name__ == "__main__":
    print("🚀 HR員工離職分析系統啟動！")
    
    # 整體統計
    總離職率 = (df['離職'] == '是').mean() * 100
    print(f"\n📋 全體員工離職率：{總離職率:.1f}%")
    
    # 執行分析
    while True:
        print("\n請選擇分析功能：")
        print("1. 互動篩選分析")
        print("2. 年齡分組分析")
        print("3. 性別×部門交叉分析")
        print("4. 顯示原始資料欄位")
        print("0. 結束程式")
        
        choice = input("\n請輸入選項 (0-4)：").strip()
        
        if choice == '1':
            filtered_data = 離職分析篩選()
        elif choice == '2':
            年齡分組分析()
        elif choice == '3':
            性別部門分析()
        elif choice == '4':
            print("\n📝 可用欄位：", list(df.columns))
        elif choice == '0':
            print("👋 分析結束，謝謝使用！")
            break
        else:
            print("❌ 無效選項，請重新輸入！")
