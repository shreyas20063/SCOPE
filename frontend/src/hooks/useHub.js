import { useState, useEffect, useCallback, useRef } from 'react';
import { useHubContext } from '../contexts/HubContext';

export function useHub(slotName) {
  const { hubState, pushToSlot: ctxPush, subscribe } = useHubContext();
  const [hubUpdated, setHubUpdated] = useState(0);
  const mountedRef = useRef(true);
  const initialLoadRef = useRef(true);

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
    return () => { mountedRef.current = false; unsub(); };
  }, [slotName, subscribe]);

  const pushToSlot = useCallback(async (data, simId) => {
    return ctxPush(slotName, data, simId);
  }, [slotName, ctxPush]);

  return { slotData, pushToSlot, isHubAvailable, hubUpdated };
}

export default useHub;
