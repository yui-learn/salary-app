# Salary App
給与明細（PDF）をアップロードし、給与データを自動で蓄積・可視化するアプリを開発しています。  
現在は、S3へアップロードされた給与明細ファイルをAWS Lambdaで処理し、  
PDFから抽出したデータをDynamoDBへ保存する機能を実装済みです。  
また、GitHub Actionsを利用し、Lambdaコードを自動デプロイするCI/CD環境を構築しています。  

## 使用技術
- Python
- AWS Lambda
- Amazon S3
- Amazon DynamoDB
- GitHub Actions

## 今後の予定
- DynamoDBからデータを取得するAPIの実装
- 給与明細アップロード機能の実装
- Amazon API GatewayによるAPI公開
- フロントエンドの開発および可視化ダッシュボード作成
- Amazon Cognitoによる認証機能の実装
