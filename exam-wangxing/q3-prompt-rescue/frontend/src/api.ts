import axios from "axios";

const client = axios.create({
  baseURL: "",
  timeout: 180_000,
});

export default client;
