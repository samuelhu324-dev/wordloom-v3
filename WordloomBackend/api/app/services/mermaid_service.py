"""
AI 结构图生成服务 - 使用 Claude 生成 Mermaid 代码

功能：
- 读取 Note 内容
- 调用 Claude 提取关键信息
- 生成 Mermaid 结构图代码
- 支持多种图表类型（流程图、思维导图等）
"""

import os
import re
from typing import Optional
from dotenv import load_dotenv
import anthropic

# 加载 .env 文件
load_dotenv()


class MermaidGenerator:
    """Mermaid 结构图生成器"""

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
        if not self.api_key:
            raise ValueError("❌ Missing ANTHROPIC_API_KEY or CLAUDE_API_KEY environment variable")
        self.client = anthropic.Anthropic(api_key=self.api_key)

    async def generate_mermaid(
        self,
        title: Optional[str],
        content: str,
        chart_type: str = "auto"
    ) -> str:
        """
        生成 Mermaid 图表代码

        Args:
            title: Note 标题
            content: Note 内容
            chart_type: 图表类型 ("auto", "flowchart", "mindmap", "timeline", "stateDiagram")

        Returns:
            Mermaid 代码字符串
        """

        # 清理内容（移除 Markdown 格式等）
        clean_content = self._clean_content(content)

        # 生成提示词
        prompt = self._build_prompt(title, clean_content, chart_type)

        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",  # 使用便宜的模型
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            mermaid_code = message.content[0].text

            # 提取代码块（如果被 ```mermaid ``` 包裹）
            mermaid_code = self._extract_code_block(mermaid_code)

            return mermaid_code

        except Exception as e:
            print(f"❌ Error generating Mermaid: {e}")
            # 返回一个简单的备用图表
            return self._generate_fallback_mermaid(title, content)

    def _clean_content(self, content: str) -> str:
        """清理内容"""
        # 移除 HTML 标签
        content = re.sub(r'<[^>]+>', '', content)
        # 移除 Markdown 链接
        content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)
        # 限制长度
        return content[:500]

    def _build_prompt(self, title: Optional[str], content: str, chart_type: str) -> str:
        """构建提示词"""

        chart_guide = {
            "flowchart": "Use flowchart TD (top-down) format to show process flow or decision making",
            "mindmap": "Use mindmap format to show hierarchical relationships and ideas",
            "timeline": "Use timeline format to show chronological events or milestones",
            "stateDiagram": "Use stateDiagram-v2 format to show state transitions",
            "auto": "Choose the most appropriate diagram type based on content (flowchart, mindmap, or timeline)"
        }

        chart_hint = chart_guide.get(chart_type, chart_guide["auto"])

        return f"""你是一个专业的结构图设计师。请根据以下笔记内容，生成一个 Mermaid 结构图代码。

笔记标题: {title or 'Untitled'}

笔记内容:
{content}

要求:
1. 生成有效的 Mermaid 语法代码
2. {chart_hint}
3. 提取核心概念和关键信息
4. 最多包含 5-8 个节点
5. 节点标签简洁清晰（中文/英文均可）
6. 只返回 Mermaid 代码，不需要其他解释

示例 flowchart 格式:
```
flowchart TD
    A["标题"] --> B["核心概念1"]
    A --> C["核心概念2"]
    B --> D["细节1"]
    C --> E["细节2"]
```

示例 mindmap 格式:
```
mindmap
  root((中心主题))
    分支1
      子项1
      子项2
    分支2
      子项3
```

现在请为上述笔记生成合适的 Mermaid 代码:"""

    def _extract_code_block(self, text: str) -> str:
        """从文本中提取代码块"""
        # 尝试提取 ```mermaid ... ``` 块
        match = re.search(r'```(?:mermaid)?\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            return match.group(1).strip()

        # 如果没有代码块，返回整个文本（假设它是有效的 Mermaid）
        return text.strip()

    def _generate_fallback_mermaid(self, title: Optional[str], content: str) -> str:
        """生成备用图表（当 API 失败时）"""
        title = title or "Untitled"
        # 从内容中提取第一句话
        first_sentence = content.split('\n')[0][:50]

        return f"""flowchart TD
    A["{title}"]
    B["核心内容"]
    C["待详细展开"]
    A --> B --> C"""


# 全局实例
try:
    mermaid_generator = MermaidGenerator()
except ValueError as e:
    print(f"⚠️ {e}")
    mermaid_generator = None
