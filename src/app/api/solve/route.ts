import { NextResponse } from 'next/server';
import { solveLocally } from '@/lib/solver';

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const matches = body.matches || [];
    const mode = body.mode || '13G';
    const solverMode = body.solver_mode || 'auto_boost';

    const solution = solveLocally(matches, mode, solverMode);
    return NextResponse.json(solution);
  } catch (err: any) {
    console.error('Next.js API Solve Error:', err);
    return NextResponse.json(
      { error: err?.message || 'Solver internal error' },
      { status: 500 }
    );
  }
}
