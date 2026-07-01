import axios from 'axios';
export const TOKEN_KEY='pe_token';
export const USER_KEY='pe_user';
const ENV=import.meta.env.VITE_API_BASE_URL;
export const API_BASE_URL=(ENV || (location.hostname==='localhost'?'http://localhost:8003':'https://proempresa-api.onrender.com')).replace(/\/$/,'');
console.log('API_BASE_URL:',API_BASE_URL);
const api=axios.create({baseURL:API_BASE_URL,headers:{'Content-Type':'application/json'}});
api.interceptors.request.use((config)=>{const t=localStorage.getItem(TOKEN_KEY); if(t) config.headers.Authorization=`Bearer ${t}`; return config;});
api.interceptors.response.use(r=>r,e=>{if(e?.response?.status===401){localStorage.removeItem(TOKEN_KEY);localStorage.removeItem(USER_KEY);} return Promise.reject(e);});
export default api;
export function setSession(data){localStorage.setItem(TOKEN_KEY,data.access_token); localStorage.setItem(USER_KEY,JSON.stringify(data.user||{}));}
export function logout(){localStorage.removeItem(TOKEN_KEY);localStorage.removeItem(USER_KEY); location.href='/login';}
export function user(){try{return JSON.parse(localStorage.getItem(USER_KEY)||'null')}catch{return null}}
export function isAuth(){return Boolean(localStorage.getItem(TOKEN_KEY))}
