import re
from typing import List, Dict, Tuple
from dataclasses import dataclass

from recursive_chunking import CustomRecursiveChunker


@dataclass
class DocumentSection:
    """文档段落结构"""
    level: int  # 标题级别
    title: str  # 标题内容
    content: str  # 段落内容
    start_pos: int  # 在原文档中的起始位置
    end_pos: int  # 在原文档中的结束位置


class StructuralChunker:
    def __init__(self, max_chunk_size: int = 2000, min_chunk_size: int = 100):
        """
        初始化结构化分块器

        Args:
            max_chunk_size: 最大块大小
            min_chunk_size: 最小块大小
        """
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size

        # Markdown标题模式
        self.md_header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)

        # HTML标题模式
        self.html_header_pattern = re.compile(r'<h([1-6])>(.*?)</h[1-6]>', re.IGNORECASE)

    def parse_markdown_structure(self, text: str) -> List[DocumentSection]:
        """解析Markdown文档结构"""
        sections = []
        lines = text.split('\n')
        current_section = None
        content_buffer = []

        for i, line in enumerate(lines):
            header_match = self.md_header_pattern.match(line)

            if header_match:
                # 保存前一个段落
                if current_section is not None:
                    current_section.content = '\n'.join(content_buffer).strip()
                    current_section.end_pos = i
                    sections.append(current_section)

                # 创建新段落
                level = len(header_match.group(1))
                title = header_match.group(2).strip()
                current_section = DocumentSection(
                    level=level,
                    title=title,
                    content="",
                    start_pos=i,
                    end_pos=i
                )
                content_buffer = []
            else:
                content_buffer.append(line)

        # 添加最后一个段落
        if current_section is not None:
            current_section.content = '\n'.join(content_buffer).strip()
            current_section.end_pos = len(lines)
            sections.append(current_section)

        return sections

    def parse_html_structure(self, text: str) -> List[DocumentSection]:
        """解析HTML文档结构"""
        sections = []
        last_end = 0

        for match in self.html_header_pattern.finditer(text):
            level = int(match.group(1))
            title = match.group(2).strip()
            start_pos = match.start()

            # 如果有前面的内容，创建一个段落
            if start_pos > last_end:
                prev_content = text[last_end:start_pos].strip()
                if prev_content:
                    sections.append(DocumentSection(
                        level=0,
                        title="",
                        content=prev_content,
                        start_pos=last_end,
                        end_pos=start_pos
                    ))

            # 查找下一个标题或文档结尾
            next_match = None
            for next_match in self.html_header_pattern.finditer(text, match.end()):
                break

            end_pos = next_match.start() if next_match else len(text)
            content = text[match.end():end_pos].strip()

            sections.append(DocumentSection(
                level=level,
                title=title,
                content=content,
                start_pos=match.start(),
                end_pos=end_pos
            ))

            last_end = end_pos

        return sections

    def merge_small_sections(self, sections: List[DocumentSection]) -> List[DocumentSection]:
        """合并过小的段落"""
        merged_sections = []
        current_merge = None

        for section in sections:
            section_size = len(section.title) + len(section.content)

            if section_size < self.min_chunk_size:
                if current_merge is None:
                    current_merge = section
                else:
                    # 合并到当前合并段落
                    current_merge.content += f"\n\n{section.title}\n{section.content}"
                    current_merge.end_pos = section.end_pos
            else:
                # 先添加之前的合并段落
                if current_merge is not None:
                    merged_sections.append(current_merge)
                    current_merge = None

                # 检查当前段落是否过大
                if section_size > self.max_chunk_size:
                    # 需要进一步分割
                    sub_chunks = self.split_large_section(section)
                    merged_sections.extend(sub_chunks)
                else:
                    merged_sections.append(section)

        # 添加最后的合并段落
        if current_merge is not None:
            merged_sections.append(current_merge)

        return merged_sections

    def split_large_section(self, section: DocumentSection) -> List[DocumentSection]:
        """分割过大的段落"""
        # 使用递归分块器处理过大的段落
        recursive_chunker = CustomRecursiveChunker(
            chunk_size=self.max_chunk_size,
            chunk_overlap=self.min_chunk_size
        )

        full_text = f"{section.title}\n{section.content}"
        sub_chunks = recursive_chunker.chunk_text(full_text)

        result = []
        for i, chunk_text in enumerate(sub_chunks):
            result.append(DocumentSection(
                level=section.level,
                title=f"{section.title}_part_{i + 1}",
                content=chunk_text,
                start_pos=section.start_pos,
                end_pos=section.end_pos
            ))

        return result

    def chunk_text(self, text: str, doc_type: str = "markdown") -> List[str]:
        """
        基于文档结构进行分块

        Args:
            text: 待分块的文档文本
            doc_type: 文档类型 ("markdown" 或 "html")

        Returns:
            分块后的文本列表
        """
        # 根据文档类型解析结构
        if doc_type.lower() == "markdown":
            sections = self.parse_markdown_structure(text)
        elif doc_type.lower() == "html":
            sections = self.parse_html_structure(text)
        else:
            raise ValueError("不支持的文档类型")

        # 合并过小的段落和分割过大的段落
        processed_sections = self.merge_small_sections(sections)

        # 生成最终的文本块
        chunks = []
        for section in processed_sections:
            if section.title:
                chunk_text = f"{section.title}\n{section.content}"
            else:
                chunk_text = section.content

            chunks.append(chunk_text.strip())

        return chunks


if __name__ == "__main__":
    # 测试结构化分块
    markdown_doc = """
    # 深度学习基础
    
    深度学习是机器学习的一个分支，使用多层神经网络来学习数据的复杂模式。
    
    ## 神经网络基础
    
    神经网络由多个节点（神经元）组成，这些节点连接在一起形成网络。每个连接都有一个权重，这些权重在训练过程中被调整。
    
    ### 激活函数
    
    激活函数决定神经元是否被激活。常见的激活函数包括ReLU、Sigmoid和Tanh。
    
    ## 卷积神经网络
    
    卷积神经网络（CNN）特别适合处理图像数据。
    
    ### 卷积层
    
    卷积层使用滤波器在输入数据上滑动，提取局部特征。
    
    ### 池化层
    
    池化层减少特征图的空间尺寸，降低计算复杂度。
    
    ## 循环神经网络
    
    循环神经网络（RNN）适合处理序列数据，如时间序列和自然语言。
    
    ### LSTM
    
    长短期记忆网络（LSTM）解决了传统RNN的梯度消失问题，能够学习长期依赖关系。
    """

    structural_chunker = StructuralChunker(max_chunk_size=300, min_chunk_size=50)
    structural_chunks = structural_chunker.chunk_text(markdown_doc, "markdown")

    print("结构化分块结果：")
    for i, chunk in enumerate(structural_chunks):
        print(f"块 {i + 1}: {chunk}\n{'=' * 50}\n")
