# 本地RAG知识库系统

这是一个基于BGE-M3嵌入模型和Chroma向量数据库的本地RAG（检索增强生成）知识库系统。该系统可以将PDF和Excel文档转换为向量数据，并提供语义搜索功能,内部支持Dify外部知识库API。

## 项目结构

- `main.py`: FastAPI服务器，提供搜索API和Dify外部知识库接口
- `ingest.py`: 文档处理脚本，用于将文档转换为向量并存储在Chroma数据库中
- `embeddings.py`: 自定义的Ollama嵌入模型实现
- `data/`: 存放要处理的文档（PDF、Excel）
- `chroma_db/`: Chroma向量数据库存储目录

## 功能特点

1. 支持PDF和Excel文档的处理
2. 使用BGE-M3嵌入模型生成高质量向量表示
3. 基于Chroma的高效向量存储和检索
4. 提供RESTful API进行语义搜索
5. 完全本地部署，无需依赖云服务
6. 支持与Dify平台集成，作为外部知识库使用
7. 提供Web界面进行API测试

## 自动化召回测试

本项目支持基于标准化测试集的自动化召回率评估，帮助用户快速了解知识库检索效果。

### 功能说明
- 自动读取 test_case_dataset/标准.md 中的所有问题和黄金答案
- 自动调用 /search API，统计Top1/Top3/Top5召回命中率
- 输出详细测试报告和csv结果文件，便于分析和持续优化

### 使用方法

1. 启动 FastAPI 检索服务（确保已完成文档向量化和服务运行）

```bash
uvicorn main:app --reload --port 8001
```

2. 运行自动化召回测试脚本

```bash
python test_case_dataset/auto_recall_eval.py
```

3. 结果说明
- 终端会输出每个问题的Top1/Top3/Top5命中情况和整体召回率
- 详细结果保存在 test_case_dataset/auto_recall_eval_result.csv

### 参数说明
- 测试用例来源：test_case_dataset/标准.md
- 检索API地址：默认 http://localhost:8001/search，可在脚本中修改
- TopK设置：默认统计Top1/Top3/Top5

### 结果解读
- Top1_hit/Top3_hit/Top5_hit：表示黄金答案是否在前K条检索结果中出现
- 召回率=命中数/总数，越高说明知识库检索效果越好

### 改进建议
- 若召回率较低，可优化分块策略、embedding模型或数据质量
- 可扩展更多测试用例，完善标准.md
- 支持自定义召回阈值、API地址等参数

## 安装与使用

### 环境要求

- Python 3.8+
- Ollama服务（需要安装bge-m3模型）

### 安装依赖

```bash
pip install -r requirements.txt
```

### 准备数据

1. 将需要处理的PDF和Excel文档放在`data/`目录下

### 处理文档

```bash
python ingest.py
```

### 启动搜索服务

```bash
uvicorn main:app --reload --port 8001
```

> **注意**: 如果端口8000已被占用，可以使用`--port`参数指定其他端口，如8001

## API使用说明

### Web测试界面

访问 http://localhost:8001/ 可以打开Web测试界面，直接在浏览器中测试API功能。

### 搜索API

- **端点**: `/search`
- **方法**: GET
- **参数**:
  - `query`: 搜索查询文本
  - `k`: 返回结果数量（默认为5）
- **返回**: 包含相关文档片段和相似度分数的JSON对象

### 示例请求

```
GET /search?query=锂离子电池安全使用&k=3
```

### 示例响应

```json
{
  "results": [
    {
      "content": "锂离子电池安全使用注意事项...",
      "score": 0.89
    },
    {
      "content": "电池组安全操作规程...",
      "score": 0.78
    },
    {
      "content": "...",
      "score": 0.65
    }
  ]
}
```

## Dify外部知识库接入说明

本系统已实现Dify外部知识库API规范，可以作为外部知识库与Dify平台集成。

### 接口说明

- **端点**: `/retrieval`
- **方法**: POST
- **请求头**:
  - `Authorization`: Bearer {API_KEY}（目前版本未实际验证API Key）
- **请求体**:
  ```json
  {
    "knowledge_id": "your-knowledge-id",
    "query": "你的问题",
    "retrieval_setting": {
      "top_k": 5,
      "score_threshold": 0.5
    }
  }
  ```
- **响应**:
  ```json
  {
    "records": [
      {
        "metadata": {
          "source": "data/example.pdf",
          "page": 1
        },
        "score": 0.89,
        "title": "example.pdf",
        "content": "文档内容片段..."
      }
    ]
  }
  ```

### 在Dify中配置步骤

1. 在Dify平台中，进入"知识库"页面，点击右上角的"外部知识库API"
2. 点击"添加外部知识库API"，填写以下信息：
   - 知识库名称：自定义一个名称
   - API接口地址：`http://localhost:8001/retrieval`（如果使用了不同端口，请相应修改）
   - API Key：任意值（当前版本未验证）
3. 点击"添加"完成API配置
4. 返回知识库页面，点击"连接外部知识库"
5. 填写知识库名称和描述，选择刚刚添加的外部知识库API
6. 填写外部知识库ID（任意值，会作为knowledge_id参数传递）
7. 调整召回设置（Top K和Score阈值）
8. 点击"创建"完成配置

## 注意事项

1. 确保Ollama服务已启动并加载了bge-m3模型
2. 大文件处理可能需要较长时间
3. 如遇到错误，请检查依赖版本兼容性
4. 与Dify集成时，确保本地服务可以被Dify平台访问（如果Dify部署在云端，需要将本地服务暴露到公网）
5. 如果启动服务时提示端口已被占用，请尝试使用其他端口

## 故障排除

### 常见问题

1. **Chroma版本兼容性问题**
   - 确保使用chromadb==0.4.22版本
   - 如遇数据库结构不匹配错误，请删除chroma_db目录并重新运行ingest.py

2. **导入错误**
   - 确保使用langchain_community而非langchain进行导入
   - 确保安装了langchain-text-splitters包

3. **嵌入模型错误**
   - 检查Ollama服务是否正常运行
   - 确认bge-m3模型是否已正确安装

4. **Dify连接问题**
   - 确保API地址正确且可访问
   - 检查请求和响应格式是否符合Dify规范

5. **端口占用问题**
   - 如果8000端口被占用，使用`--port 8001`（或其他可用端口）启动服务
   - 可以使用`lsof -i:端口号`命令查看占用端口的进程

## 未来改进计划

1. 添加更完善的用户界面，方便查询和管理
2. 支持更多文档格式（如Word、HTML等）
3. 添加文档元数据管理功能
4. 优化文本分块策略，提高检索质量
5. 增加多语言支持
6. 增强与Dify的集成，支持更多功能 