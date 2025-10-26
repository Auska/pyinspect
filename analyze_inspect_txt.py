import os
import argparse
from zai import ZhipuAiClient

# 初始化AI客户端
client = ZhipuAiClient(api_key=os.getenv('ZHIPUAI_API_KEY'))

def read_inspect_file(file_path):
    """读取inspect.txt文件内容"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def analyze_with_ai(content):
    """使用AI大模型分析内容"""
    try:
        response = client.chat.completions.create(
            model="glm-4.5-flash",
            messages=[
                {
                    "role": "system",
                    "content": "你是一个网络设备巡检专家，能够分析设备巡检日志并识别潜在问题。"
                },
                {
                    "role": "user",
                    "content": f"请分析以下网络设备巡检日志，识别任何潜在的问题或异常，并提供简要的总结报告（1.设备的基本情况；2.每台设备存在的问题异常；3.总结）：\n\n{content}"
                }
            ],
            temperature=0.0
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"分析过程中出现错误: {str(e)}"


def main():
    # 设置命令行参数解析
    parser = argparse.ArgumentParser(description='分析网络设备巡检日志')
    parser.add_argument('-i', '--input', default='inspect.txt', 
                        help='巡检日志文件路径 (默认: inspect.txt)')
    parser.add_argument('-o', '--output', default='analysis_report.txt',
                        help='分析报告输出文件路径 (默认: analysis_report.txt)')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 读取巡检日志文件
    if not os.path.exists(args.input):
        print(f"错误: 文件 {args.input} 不存在")
        return

    content = read_inspect_file(args.input)

    # 调用AI分析
    print("正在分析巡检日志...")
    analysis_result = analyze_with_ai(content)

    # 输出结果
    print("\n=== AI分析结果 ===")
    print(analysis_result)

    # 保存结果到文件
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(analysis_result)
    print(f"\n分析报告已保存到 {args.output}")


if __name__ == "__main__":
    main()
