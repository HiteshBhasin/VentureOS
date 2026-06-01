interface DetailPageProps {
  params: Promise<{ id: string }>;
}

export default async function DetailPage({ params }: DetailPageProps) {
  const { id } = await params;
  return (
    <div className="flex h-full items-center justify-center bg-[#080c18] font-mono">
      <span className="text-[11px] tracking-widest text-zinc-600 uppercase">Detail: {id}</span>
    </div>
  );
}

