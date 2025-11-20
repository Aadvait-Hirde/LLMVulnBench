import { Router, Request, Response } from 'express';
import { ModelLoader } from '../models/ModelLoader';

const router = Router();
const modelLoader = new ModelLoader();

router.post('/', async (req: Request, res: Response) => {
  try {
    const { features } = req.body;
    
    if (!features || !Array.isArray(features)) {
      return res.status(400).json({ error: 'Invalid input: features must be an array' });
    }

    const model = await modelLoader.loadModel();
    const prediction = await modelLoader.predict(model, features);
    
    res.json({ prediction });
  } catch (error) {
    res.status(500).json({ error: 'Prediction failed', message: error instanceof Error ? error.message : 'Unknown error' });
  }
});

export default router;
