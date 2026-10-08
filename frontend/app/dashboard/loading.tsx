import { Skeleton } from "@/src/components/ui/Skeleton";
export default function Loading() {
  return <main className="mx-auto w-full max-w-6xl space-y-7 p-5 sm:p-8" aria-label="Loading workspace" role="status"><Skeleton className="h-10 w-64" /><Skeleton className="h-32 w-full" /><div className="grid grid-cols-2 gap-4 lg:grid-cols-4">{[0,1,2,3].map(i => <Skeleton key={i} className="h-32 w-full" />)}</div><Skeleton className="h-72 w-full" /></main>;
}
