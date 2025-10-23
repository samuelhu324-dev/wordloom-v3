import axios from "axios";

/** Same-origin base; actual path resolved by routes/map-api.ts */
export const api = axios.create({
  baseURL: "",
  withCredentials: false,
});
