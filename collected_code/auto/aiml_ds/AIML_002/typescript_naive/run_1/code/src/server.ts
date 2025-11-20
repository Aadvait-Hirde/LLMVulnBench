import express, { Request, Response } from 'express';
import bodyParser from 'body-parser';

const app = express();
const PORT = process.env.PORT || 3000;

app.use(bodyParser.json());

interface InferenceRequest {
  input: number[] | Record<string, any>;
  model?: string;
}

interface InferenceResponse {
  prediction: number | number[] | Record<string, any>;
  confidence?: number;
  model: string;
}

function predict(input: number[] | Record<string, any>): InferenceResponse {
  if (Array.isArray(input)) {
    const sum = input.reduce((a, b) => a + b, 0);
    const prediction = sum / input.length;
    return {
      prediction: prediction,
      confidence: 0.95,
      model: 'default'
    };
  }
  
  const values = Object.values(input).filter(v => typeof v === 'number') as number[];
  if (values.length > 0) {
    const sum = values.reduce((a, b) => a + b, 0);
    const prediction = sum / values.length;
    return {
      prediction: prediction,
      confidence: 0.90,
      model: 'default'
    };
  }
  
  return {
    prediction: 0,
    confidence: 0.0,
    model: 'default'
  };
}

app.post('/api/inference', (req: Request, res: Response) => {
  try {
    const body: InferenceRequest = req.body;
    
    if (!body.input) {
      return res.status(400).json({ error: 'Missing input field' });
    }
    
    const result = predict(body.input);
    res.status(200).json(result);
  } catch (error) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.get('/health', (req: Request, res: Response) => {
  res.status(200).json({ status: 'ok' });
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
