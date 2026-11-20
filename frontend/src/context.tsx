import { createContext, useContext } from 'react';
import type { User } from './types';
export const Auth = createContext<{user:User|null;setUser:(user:User|null)=>void}>({user:null,setUser:()=>{}});
export function useAuth(){return useContext(Auth)}
