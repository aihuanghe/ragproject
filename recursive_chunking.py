from typing import List, Optional


class CustomRecursiveChunker:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100,
                 separators: Optional[List[str]] = None):
        """
        初始化递归分块器

        Args:
            chunk_size: 目标块大小
            chunk_overlap: 块间重叠大小
            separators: 分隔符列表，按优先级排序
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # 默认分隔符，按优先级从高到低
        if separators is None:
            self.separators = [
                "\n\n",  # 段落分隔符
                "\n",  # 行分隔符
                "。",  # 中文句号
                ".",  # 英文句号
                "！",  # 中文感叹号
                "!",  # 英文感叹号
                "？",  # 中文问号
                "?",  # 英文问号
                "；",  # 中文分号
                ";",  # 英文分号
                "，",  # 中文逗号
                ",",  # 英文逗号
                " ",  # 空格
                ""  # 字符级别分割
            ]
        else:
            self.separators = separators

    def split_text_by_separator(self, text: str, separator: str) -> List[str]:
        """根据指定分隔符分割文本"""
        if separator == "":
            # 字符级别分割
            return list(text)

        parts = text.split(separator)
        result = []

        for i, part in enumerate(parts):
            if i == 0:
                result.append(part)
            else:
                # 保留分隔符
                result.append(separator + part)

        return [part for part in result if part.strip()]

    def merge_splits(self, splits: List[str]) -> List[str]:
        """
        将小的分割合并成符合大小要求的块

        Args:
            splits: 分割后的文本片段列表

        Returns:
            合并后的文本块列表
        """
        chunks = []
        current_chunk = ""

        for split in splits:
            # 检查添加当前分割是否会超过块大小限制
            if len(current_chunk) + len(split) <= self.chunk_size:
                current_chunk += split
            else:
                # 如果当前块不为空，添加到结果中
                if current_chunk:
                    chunks.append(current_chunk.strip())

                # 开始新的块
                if len(split) <= self.chunk_size:
                    current_chunk = split
                else:
                    # 如果单个分割就超过块大小，需要进一步递归分割
                    sub_chunks = self.recursive_split(split)
                    chunks.extend(sub_chunks[:-1])  # 添加除最后一个外的所有块
                    current_chunk = sub_chunks[-1] if sub_chunks else ""

        # 添加最后一个块
        if current_chunk:
            chunks.append(current_chunk.strip())

        return self.add_overlap(chunks)

    def add_overlap(self, chunks: List[str]) -> List[str]:
        """为块添加重叠内容"""
        if len(chunks) <= 1 or self.chunk_overlap == 0:
            return chunks

        overlapped_chunks = [chunks[0]]

        for i in range(1, len(chunks)):
            prev_chunk = chunks[i - 1]
            current_chunk = chunks[i]

            # 从前一个块的末尾提取重叠内容
            overlap_start = max(0, len(prev_chunk) - self.chunk_overlap)
            overlap_text = prev_chunk[overlap_start:]

            # 将重叠内容添加到当前块的开头
            overlapped_chunk = overlap_text + current_chunk
            overlapped_chunks.append(overlapped_chunk)

        return overlapped_chunks

    def recursive_split(self, text: str) -> List[str]:
        """
        递归分割文本

        Args:
            text: 待分割的文本

        Returns:
            分割后的文本块列表
        """
        # 如果文本小于等于块大小，直接返回
        if len(text) <= self.chunk_size:
            return [text]

        # 尝试使用每个分隔符进行分割
        for separator in self.separators:
            splits = self.split_text_by_separator(text, separator)

            # 如果分割成功（产生多个部分）
            if len(splits) > 1:
                result = []
                for split in splits:
                    # 对每个分割递归处理
                    sub_result = self.recursive_split(split)
                    result.extend(sub_result)

                # 合并小的分割
                return self.merge_splits(result)

        # 如果所有分隔符都无法分割，强制按字符分割
        return [text[i:i + self.chunk_size] for i in range(0, len(text), self.chunk_size)]

    def chunk_text(self, text: str) -> List[str]:
        """主要的分块方法"""
        return self.recursive_split(text)



