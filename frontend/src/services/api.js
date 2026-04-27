import axios from 'axios';
const BASE = import.meta.env.VITE_API_URL || 'https://kiruba1509kk-cinephy-backend.hf.space';
export const api = {
  recommend: {
    byTitle: (title, n = 5) => axios.post(${BASE}/recommend, { title, n }),
    byUser:  (user_id, n = 10) => axios.post(${BASE}/recommend, { user_id, n }),
  },
  movies: {
    detail: (id) => axios.get(${BASE}/movie/),
    search: (q)  => axios.get(${BASE}/movies/search, { params: { q } }),
    top: (n = 10, genre = null) =>
      axios.get(${BASE}/movies/top, { params: genre ? { n, genre } : { n } }),
  },
  user: {
    profile:       (user_id) => axios.get(${BASE}/user/),
    getHistory:    (user_id) => axios.get(${BASE}/user/history/),
    saveHistory:   (data)    => axios.post(${BASE}/user/history, data),
    deleteHistory: (user_id) => axios.delete(${BASE}/user/history/),
    rate:          (data)    => axios.post(${BASE}/user/rate, data),
  }
};
