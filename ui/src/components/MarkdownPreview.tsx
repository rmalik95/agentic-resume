import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface Props {
  content: string;
}

export default function MarkdownPreview({ content }: Props) {
  return (
    <div className="md-preview text-[15px] text-text-primary leading-relaxed">
      <Markdown remarkPlugins={[remarkGfm]}>{content}</Markdown>
    </div>
  );
}
