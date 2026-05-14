interface DetailPageProps {
  params: {
    id: string;
  };
}

export default function DetailPage({ params }: DetailPageProps) {
  return (
    <div className="flex h-full items-center justify-center bg-[#080c18] font-mono">
      <span className="text-[11px] tracking-widest text-zinc-600 uppercase">Detail: {params.id}</span>
    </div>
  );
}

