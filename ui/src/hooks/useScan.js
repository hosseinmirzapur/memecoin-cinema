import { useCallback, useReducer, useRef } from 'react';
import { scan } from '@/api.js';

// run counts scans so the view can key itself per scan and replay from the top.
const IDLE = { phase: 'idle', run: 0, chain: null, address: null, sources: {}, agent: null, result: null, error: null, focus: null };

function reducer(state, action) {
  switch (action.type) {
    case 'start':
      return { ...IDLE, run: state.run + 1, phase: 'running', chain: action.chain, address: action.address, focus: 'token_info' };
    case 'source':
      return { ...state, sources: { ...state.sources, [action.name]: action.payload }, focus: action.name };
    case 'agent':
      return { ...state, agent: action.payload, focus: 'agent' };
    case 'done':
      return { ...state, phase: action.result.ok === false ? 'blocked' : 'done', result: action.result, focus: 'verdict' };
    case 'error':
      return { ...state, phase: 'error', error: action.error };
    case 'reset':
      return { ...IDLE, run: state.run };
    default:
      return state;
  }
}

// Owns one scan at a time. A new scan aborts the one in flight. onEvent sees every streamed frame.
export function useScan(onEvent) {
  const [state, dispatch] = useReducer(reducer, IDLE);
  const controller = useRef(null);
  const listener = useRef(onEvent);
  listener.current = onEvent;

  const start = useCallback(async (chain, address) => {
    controller.current?.abort();
    const mine = new AbortController();
    controller.current = mine;
    dispatch({ type: 'start', chain, address });
    try {
      await scan(
        chain,
        address,
        (kind, payload) => {
          listener.current?.(kind, payload);
          if (kind === 'source') dispatch({ type: 'source', name: payload.name, payload });
          else if (kind === 'agent') dispatch({ type: 'agent', payload });
          else if (kind === 'done') dispatch({ type: 'done', result: payload });
          else if (kind === 'error') dispatch({ type: 'error', error: payload.error });
        },
        mine.signal,
      );
    } catch (err) {
      if (err.name !== 'AbortError') dispatch({ type: 'error', error: err.message });
    }
  }, []);

  const reset = useCallback(() => {
    controller.current?.abort();
    dispatch({ type: 'reset' });
  }, []);

  return { state, start, reset };
}
