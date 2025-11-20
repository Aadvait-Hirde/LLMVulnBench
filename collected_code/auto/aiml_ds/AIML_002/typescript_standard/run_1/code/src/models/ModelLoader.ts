import * as tf from '@tensorflow/tfjs-node';
import { LayersModel } from '@tensorflow/tfjs-node';

export class ModelLoader {
  private modelPath: string;
  private model: LayersModel | null = null;

  constructor(modelPath: string = './model/model.json') {
    this.modelPath = modelPath;
  }

  async loadModel(): Promise<LayersModel> {
    if (this.model) {
      return this.model;
    }

    try {
      this.model = await tf.loadLayersModel(`file://${this.modelPath}`);
      return this.model;
    } catch (error) {
      throw new Error(`Failed to load model: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async predict(model: LayersModel, features: number[]): Promise<number | number[]> {
    const inputTensor = tf.tensor2d([features]);
    const prediction = model.predict(inputTensor) as tf.Tensor;
    const result = await prediction.data();
    inputTensor.dispose();
    prediction.dispose();
    
    return result.length === 1 ? result[0] : Array.from(result);
  }
}
