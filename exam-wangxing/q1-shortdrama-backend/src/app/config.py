"""环境配置：Stripe webhook secret、时间窗等。"""
import os

DATABASE_PATH = os.environ.get("DATABASE_PATH", "./data/app.db")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "whsec_test_local_default_secret")
# Stripe 风格验签容忍秒数（与测试/脚本一致）
STRIPE_SIGNATURE_TOLERANCE_SECONDS = int(os.environ.get("STRIPE_SIGNATURE_TOLERANCE_SECONDS", "300"))
# Apple mock：可选共享密钥校验（真实环境为 JWS + Apple 根证书）
APPLE_SHARED_SECRET = os.environ.get("APPLE_SHARED_SECRET", "apple_shared_mock_secret")

API_PREFIX = os.environ.get("API_PREFIX", "")
