#!/usr/bin/env python3
"""
バックエンドサーバー起動スクリプト
"""

import os
import sys
import subprocess

# バックエンドディレクトリのパス
backend_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'backend')
backend_dir = os.path.abspath(backend_dir)

print(f"バックエンドディレクトリ: {backend_dir}")

# 作業ディレクトリを変更
os.chdir(backend_dir)

# Pythonパスにバックエンドディレクトリを追加
sys.path.insert(0, backend_dir)

try:
    # main.pyから直接アプリケーションを起動
    print("🚀 バックエンドサーバーを起動中...")
    
    import uvicorn
    from main import app
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
    
except ImportError as e:
    print(f"❌ インポートエラー: {e}")
    print("必要なモジュールがインストールされていません")
    
    # 代替案: subprocess で実行
    try:
        print("📦 subprocess経由で起動を試行...")
        subprocess.run([
            sys.executable, "-m", "uvicorn", "main:app",
            "--reload", "--host", "0.0.0.0", "--port", "8000"
        ], cwd=backend_dir)
    except Exception as e2:
        print(f"❌ subprocess実行エラー: {e2}")
        
except Exception as e:
    print(f"❌ 起動エラー: {e}")
    import traceback
    traceback.print_exc()