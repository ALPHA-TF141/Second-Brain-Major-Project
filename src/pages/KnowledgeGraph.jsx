import React from 'react';
import { useNavigate } from 'react-router-dom';
import InteractiveKnowledgeGraphEngine from '../components/InteractiveKnowledgeGraphEngine.jsx';

export default function KnowledgeGraphPage() {
  const navigate = useNavigate();

  return (
    <div className="relative h-full w-full overflow-hidden bg-[#111318]">
      <InteractiveKnowledgeGraphEngine
        onAskAI={(topic) => {
          navigate(`/?ask=${encodeURIComponent(`Explain everything connected to ${topic}`)}`);
        }}
        onOpenItem={(node) => {
          console.log('Opened node:', node);
        }}
      />
    </div>
  );
}
