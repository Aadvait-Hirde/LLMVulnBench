import express from 'express';
import predictRouter from './routes/predict';

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());
app.use('/predict', predictRouter);

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
