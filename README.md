# Salary App
自身の給与明細をアップロードして自動で給与テーブルを作成するアプリを開発中です。  
現時点では、AWSのS3に給与明細をアップロードするとlambdaでPDFからテキスト抽出し、DynamoDBに保存する工程まで完了してます。  
また、GitHub Actionsの仕組みをデプロイしました。

## 使用技術
- Python
- AWS Lambda
- GitHub Actions

## 今後の予定
- DynamoDBにあるデータを取得するLambdaデプロイ
- ダッシュボードから給与明細ファイルをアップロードし、S3に保存するLambdaデプロイ
- API GatewayでHTTPS APIの作成
- 可視化ダッシュボード(フロントエンド)開発
- Amazon Cognitoによるパスワード認証
