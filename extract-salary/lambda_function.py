import re
import json
import io
import boto3
import pdfplumber
import urllib.parse

# S3を操作するためのboto3クライアントを初期化
s3_client = boto3.client('s3')

def extract_salary_data(pdf_text):
    extracted_data = {
        "EmployeeId": "",    # 社員番号 パーティションキー
        "YearMonth": "",     # ソートキー
        "BasePay": 0,        
        "JobAllowance": 0,   
        "CommuterPass": 0,   
        "TotalAllowance": 0, 
        "TotalDeduction": 0, 
        "NetPay": 0          
    }

    # 社員番号の抽出
    emp_match = re.search(r"社員番号\s*[:：]?\s*(\d+)", pdf_text)
    if emp_match:
        extracted_data["EmployeeId"] = emp_match.group(1)

    # 給与・賞与のタイトルから年月と種別を抽出
    type_match = re.search(r"(\d{4}年\d{2}月給与|\d{4}年\w+賞与)", pdf_text)
    if type_match:
        raw_title = type_match.group(1) # 例: "2025年冬季賞与" や "2026年04月給与"
        
        # 先頭の4桁（年）を安全に取得
        year = raw_title[0:4] 
        
        # 賞与（ボーナス）のパターンのとき
        if "賞与" in raw_title:
            type_sign = "bonus"
            if "夏季" in raw_title:
                month = "06"
            elif "冬季" in raw_title:
                month = "12"
            else:
                month = "00" # 防衛策
                
        # 通常の給与のパターンのとき
        else:
            type_sign = "salary"
            # 「〇〇月」の数字2桁を抜き出す（例: "2026年04月給与" から "04" を取る）
            month = raw_title[5:7] 

        # 綺麗に合体させて、DynamoDBのソートキー用データにする
        extracted_data["YearMonth"] = f"{year}-{month}-{type_sign}" # 例: "2025-12-bonus"

    # 各種金額の抽出（それぞれの項目が独立して抽出できるようにインデントを独立させている）
    base_match = re.search(r"(?:基本給/月俸|賞与)\s*([\d,]+)", pdf_text)
    if base_match:
        extracted_data["BasePay"] = int(base_match.group(1).replace(',', ''))

    job_match = re.search(r"職務手当\s*([\d,]+)", pdf_text)
    if job_match:
        extracted_data["JobAllowance"] = int(job_match.group(1).replace(',', ''))

    commute_match = re.search(r"通勤手当\s*([\d,]+)", pdf_text)
    if commute_match:
        extracted_data["CommuterPass"] = int(commute_match.group(1).replace(',', ''))

    total_allow_match = re.search(r"支給合計額\s*([\d,]+)", pdf_text)
    if total_allow_match:
        extracted_data["TotalAllowance"] = int(total_allow_match.group(1).replace(',', ''))

    total_deduct_match = re.search(r"控除合計額\s*([-]?[\d,]+)", pdf_text)
    if total_deduct_match:
        extracted_data["TotalDeduction"] = int(total_deduct_match.group(1).replace(',', ''))

    net_match = re.search(r"差引支給額\s*([\d,]+)", pdf_text)
    if net_match:
        extracted_data["NetPay"] = int(net_match.group(1).replace(',', ''))

    return extracted_data


def lambda_handler(event, context):
    """
    S3にPDFがアップロードされた時に自動起動するメイン関数
    """
    try:
        # 1. S3イベントからバケット名とファイル名（キー）を自動取得
        bucket_name = event['Records'][0]['s3']['bucket']['name']
        raw_file_key = event['Records'][0]['s3']['object']['key']

        file_key = urllib.parse.unquote_plus(raw_file_key)
        
        print(f"=== [S3検知] バケット: {bucket_name}, ファイル: {file_key} ===")
        
        # 2. S3からPDFファイルの「バイナリデータ（生データ）」をダウンロード
        s3_response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        pdf_bytes = s3_response['Body'].read()
        
        # 3. メモリ上でPDFを開き、テキストを抽出（ローカルのファイルオープンの代わり）
        pdf_text = ""
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                pdf_text += page.extract_text() or ""
        
        # 【デバッグ用】CloudWatchで抽出テキストを確認
        print("=== [CloudWatch Log] S3から抽出した生テキスト ===")
        print(pdf_text)
        print("==============================================")
        
        # 4. 完成した正規表現ロジックでJSONデータを作成
        result = extract_salary_data(pdf_text)
        
        # 【デバッグ用】CloudWatchでパズル結果を確認
        print("=== [CloudWatch Log] 抽出成功データ ===")
        print(json.dumps(result, ensure_ascii=False, indent=4))
        
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('Salary')
        table.put_item(Item=result)  
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'PDFの処理が正常に完了しました', 'data': result}, ensure_ascii=False)
        }
        
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }