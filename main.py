from fastapi import FastAPI, Header, HTTPException, Request
from langchain_community.vectorstores import Chroma
from embeddings import OllamaEmbeddings
from typing import Dict, List, Optional, Union
import json
from fastapi.responses import HTMLResponse

app = FastAPI()

# 初始化 Embedding 和 VectorStore
embeddings = OllamaEmbeddings()
vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings
)

@app.get("/search")
async def search(query: str, k: int = 5):
    results = vectorstore.similarity_search_with_score(query, k=k)
    formatted = [{"content": doc.page_content, "score": score} for doc, score in results]
    return {"results": formatted}

# Dify外部知识库API
@app.post("/retrieval")
async def retrieval(request: Request):
    # 验证Authorization头
    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=403,
            detail={"error_code": 1001, "error_msg": "无效的 Authorization 头格式。预期格式为 'Bearer API_KEY'。"}
        )
    
    # 这里可以添加API Key验证逻辑
    # api_key = authorization.replace("Bearer ", "")
    # if api_key != "your-api-key":
    #     raise HTTPException(
    #         status_code=403,
    #         detail={"error_code": 1002, "error_msg": "授权失败。"}
    #     )
    
    # 解析请求体
    try:
        body = await request.json()
        knowledge_id = body.get("knowledge_id")
        query = body.get("query")
        retrieval_setting = body.get("retrieval_setting", {})
        
        # 参数验证
        if not knowledge_id or not query:
            raise HTTPException(status_code=400, detail="knowledge_id和query是必需的")
        
        top_k = retrieval_setting.get("top_k", 5)
        score_threshold = retrieval_setting.get("score_threshold", 0.5)
        
        # 执行检索
        results = vectorstore.similarity_search_with_score(query, k=top_k)
        
        # 过滤结果并格式化为Dify要求的格式
        records = []
        for doc, score in results:
            if score >= score_threshold:
                # 提取文档元数据
                metadata = doc.metadata if hasattr(doc, "metadata") else {}
                # 提取标题，如果没有则使用文件名或默认值
                title = metadata.get("source", "未知文档")
                if "/" in title:
                    title = title.split("/")[-1]
                
                records.append({
                    "content": doc.page_content,
                    "score": float(score),  # 确保score是浮点数
                    "title": title,
                    "metadata": metadata
                })
        
        return {"records": records}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="无效的JSON请求体")
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error_code": 500, "error_msg": str(e)})

@app.get("/", response_class=HTMLResponse)
async def get_test_form():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>RAG知识库测试</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            .container {
                display: flex;
                flex-direction: column;
                gap: 20px;
            }
            .card {
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            h1, h2 {
                color: #333;
            }
            input, textarea, button {
                padding: 8px;
                margin: 5px 0;
                border-radius: 4px;
                border: 1px solid #ccc;
            }
            button {
                background-color: #4CAF50;
                color: white;
                border: none;
                cursor: pointer;
            }
            button:hover {
                background-color: #45a049;
            }
            pre {
                background-color: #f5f5f5;
                padding: 10px;
                border-radius: 4px;
                overflow-x: auto;
            }
            .form-group {
                margin-bottom: 15px;
            }
            label {
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <h1>RAG知识库测试工具</h1>
        
        <div class="container">
            <div class="card">
                <h2>搜索API测试</h2>
                <div class="form-group">
                    <label for="search-query">查询内容:</label>
                    <input type="text" id="search-query" placeholder="输入搜索内容..." style="width: 70%;">
                    <input type="number" id="search-k" value="5" min="1" max="20" style="width: 50px;">
                </div>
                <button onclick="testSearch()">搜索</button>
                <div>
                    <h3>结果:</h3>
                    <pre id="search-result">结果将显示在这里...</pre>
                </div>
            </div>
            
            <div class="card">
                <h2>Dify外部知识库API测试</h2>
                <div class="form-group">
                    <label for="retrieval-query">查询内容:</label>
                    <input type="text" id="retrieval-query" placeholder="输入查询内容..." style="width: 100%;">
                </div>
                <div class="form-group">
                    <label for="knowledge-id">知识库ID:</label>
                    <input type="text" id="knowledge-id" value="test-knowledge" style="width: 100%;">
                </div>
                <div class="form-group">
                    <label for="api-key">API Key:</label>
                    <input type="text" id="api-key" value="test-api-key" style="width: 100%;">
                </div>
                <div class="form-group">
                    <label for="top-k">Top K:</label>
                    <input type="number" id="top-k" value="3" min="1" max="20">
                </div>
                <div class="form-group">
                    <label for="score-threshold">Score阈值:</label>
                    <input type="number" id="score-threshold" value="0.5" min="0" max="1" step="0.1">
                </div>
                <button onclick="testRetrieval()">查询</button>
                <div>
                    <h3>结果:</h3>
                    <pre id="retrieval-result">结果将显示在这里...</pre>
                </div>
            </div>
        </div>

        <script>
            async function testSearch() {
                const query = document.getElementById('search-query').value;
                const k = document.getElementById('search-k').value;
                const resultElement = document.getElementById('search-result');
                
                if (!query) {
                    resultElement.textContent = '请输入查询内容';
                    return;
                }
                
                resultElement.textContent = '加载中...';
                
                try {
                    const response = await fetch(`/search?query=${encodeURIComponent(query)}&k=${k}`);
                    const data = await response.json();
                    resultElement.textContent = JSON.stringify(data, null, 2);
                } catch (error) {
                    resultElement.textContent = `错误: ${error.message}`;
                }
            }
            
            async function testRetrieval() {
                const query = document.getElementById('retrieval-query').value;
                const knowledgeId = document.getElementById('knowledge-id').value;
                const apiKey = document.getElementById('api-key').value;
                const topK = document.getElementById('top-k').value;
                const scoreThreshold = document.getElementById('score-threshold').value;
                const resultElement = document.getElementById('retrieval-result');
                
                if (!query || !knowledgeId) {
                    resultElement.textContent = '查询内容和知识库ID是必需的';
                    return;
                }
                
                resultElement.textContent = '加载中...';
                
                try {
                    const response = await fetch('/retrieval', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${apiKey}`
                        },
                        body: JSON.stringify({
                            knowledge_id: knowledgeId,
                            query: query,
                            retrieval_setting: {
                                top_k: parseInt(topK),
                                score_threshold: parseFloat(scoreThreshold)
                            }
                        })
                    });
                    
                    if (!response.ok) {
                        throw new Error(`HTTP错误: ${response.status}`);
                    }
                    
                    const data = await response.json();
                    resultElement.textContent = JSON.stringify(data, null, 2);
                } catch (error) {
                    resultElement.textContent = `错误: ${error.message}`;
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)