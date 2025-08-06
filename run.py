# run.py
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=18080,
        reload=False,    # 生产环境关闭 reload
        workers=1        # 使用单进程，确保内存共享
    )

# nohup python run.py > run.log 2>&1 &