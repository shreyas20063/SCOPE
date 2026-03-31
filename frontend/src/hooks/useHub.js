import { useState, useEffect, useCallback, useRef } from 'react';
import { useHubContext } from '../contexts/HubContext';

export function useHub(slotName) {
  const { hubState, pushToSlot: ctxPush, subscribe } = useHubContext();
  const [hubUpdated, setHubUpdated] = useState(0);
  const [isPushing, setIsPushing] = useState(false);
  const [pushResult, setPushResult] = useState(null); // { success, enriched, warning, error }
  const mountedRef = useRef(true);
  const initialLoadRef = useRef(true);
  const pushResultTimerRef = useRef(null);

  const slotData = hubState[slotName] || null;
  const isHubAvailable = slotData !== null;

  useEffect(() => {
    mountedRef.current = true;
    const unsub = subscribe(slotName, () => {
      if (mountedRef.current && !initialLoadRef.current) {
        setHubUpdated(prev => prev + 1);
      }
    });
    initialLoadRef.current = false;
    return () => {
      mountedRef.current = false;
      unsub();
      if (pushResultTimerRef.current) clearTimeout(pushResultTimerRef.current);
    };
  }, [slotName, subscribe]);

  const pushToSlot = useCallback(async (data, simId) => {
    setIsPushing(true);
    setPushResult(null);
    try {
      const result = await ctxPush(slotName, data, simId);
      if (mountedRef.current) {
        setPushResult(result);
        // Auto-clear result after 4 seconds
        pushResultTimerRef.current = setTimeout(() => {
          if (mountedRef.current) setPushResult(null);
        }, 4000);
      }
      return result;
    } catch (err) {
      const errResult = { success: false, error: err.message || 'Push failed' };
      if (mountedRef.current) {
        setPushResult(errResult);
        pushResultTimerRef.current = setTimeout(() => {
          if (mountedRef.current) setPushResult(null);
        }, 4000);
      }
      return errResult;
    } finally {
      if (mountedRef.current) setIsPushing(false);
    }
  }, [slotName, ctxPush]);

  const clearPushResult = useCallback(() => {
    setPushResult(null);
    if (pushResultTimerRef.current) clearTimeout(pushResultTimerRef.current);
  }, []);

  return {
    slotData,
    pushToSlot,
    isHubAvailable,
    hubUpdated,
    isPushing,
    pushResult,
    clearPushResult,
  };
}

export default useHub;
