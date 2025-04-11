const fs = require('fs');
const path = require('path');
const { v4: uuidv4 } = require('uuid');
const ffmpeg = require('fluent-ffmpeg');
const { OpenAI } = require('openai');
const os = require('os');
const config = require('../config');

// Set FFmpeg path
const ffmpegPath = require('ffmpeg-static');
ffmpeg.setFfmpegPath(ffmpegPath);

// Create OpenAI client
const openai = new OpenAI({
  apiKey: config.OPENAI_API_KEY
});

// Split audio file into chunks
const splitAudioFile = async (audioBuffer, maxChunkSizeBytes, originalFileName) => {
  const fileNameWithoutExt = path.parse(originalFileName).name;
  const fileExtension = path.extname(originalFileName);
  const chunks = [];
  const tempDir = path.join(os.tmpdir(), uuidv4());

  try {
    // Create temp directory
    fs.mkdirSync(tempDir, { recursive: true });

    // Write the original audio buffer to a temporary file
    const tempInputPath = path.join(tempDir, originalFileName);
    fs.writeFileSync(tempInputPath, audioBuffer);

    // Determine if the file is an MP3
    let tempMp3Path;
    if (fileExtension.toLowerCase() === '.mp3') {
      console.log('Input is an MP3 file. Skipping conversion.');
      tempMp3Path = tempInputPath;
    } else {
      console.log('Converting input audio to MP3 format.');
      tempMp3Path = path.join(tempDir, `${fileNameWithoutExt}_converted.mp3`);
      await convertAudioToMp3(tempInputPath, tempMp3Path);
    }

    // Get file information using FFmpeg
    const fileInfo = await getFileInfo(tempMp3Path);
    const totalSize = parseInt(fileInfo.format.size || 0);
    const duration = parseFloat(fileInfo.format.duration || 0);

    // Calculate the number of chunks needed
    const numChunks = Math.max(1, Math.ceil(totalSize / maxChunkSizeBytes));

    // Calculate chunk duration
    const chunkDuration = duration / numChunks;

    console.log(`Total size: ${totalSize}`);
    console.log(`Duration: ${duration}`);
    console.log(`Splitting into ${numChunks} chunks of ${chunkDuration} seconds each.`);

    // Split the audio file into chunks
    const outputPattern = path.join(tempDir, `${fileNameWithoutExt}_chunk_%03d.mp3`);
    await splitFile(tempMp3Path, outputPattern, chunkDuration);

    // Collect chunk files
    const chunkFiles = fs.readdirSync(tempDir)
      .filter(f => f.startsWith(`${fileNameWithoutExt}_chunk_`) && f.endsWith('.mp3'))
      .sort();

    // Process each chunk
    for (const chunkFileName of chunkFiles) {
      const chunkPath = path.join(tempDir, chunkFileName);
      const chunkData = fs.readFileSync(chunkPath);
      const chunkSize = chunkData.length;

      if (chunkSize <= maxChunkSizeBytes) {
        chunks.push({
          data: chunkData,
          size: chunkSize,
          file_name: chunkFileName
        });
      } else {
        console.error(`Chunk ${chunkFileName} exceeds the maximum size after splitting.`);
        throw new Error('Chunk size exceeds the maximum size after splitting.');
      }
    }

    return chunks;
  } catch (error) {
    console.error('Error splitting audio file:', error);
    throw error;
  } finally {
    // Clean up temporary files
    try {
      fs.rmSync(tempDir, { recursive: true, force: true });
    } catch (error) {
      console.error('Error cleaning up temporary files:', error);
    }
  }
};

// Convert audio to MP3
const convertAudioToMp3 = (inputPath, outputPath) => {
  return new Promise((resolve, reject) => {
    ffmpeg(inputPath)
      .output(outputPath)
      .format('mp3')
      .audioCodec('libmp3lame')
      .audioBitrate(192)
      .on('end', () => {
        console.log(`Converted MP3 file size: ${Math.round(fs.statSync(outputPath).size / 1024 / 1024)} MB`);
        resolve();
      })
      .on('error', (err) => {
        console.error('Error converting audio to MP3:', err);
        reject(err);
      })
      .run();
  });
};

// Get file information
const getFileInfo = (filePath) => {
  return new Promise((resolve, reject) => {
    ffmpeg.ffprobe(filePath, (err, metadata) => {
      if (err) {
        return reject(err);
      }
      resolve(metadata);
    });
  });
};

// Split file
const splitFile = (inputPath, outputPattern, chunkDuration) => {
  return new Promise((resolve, reject) => {
    ffmpeg(inputPath)
      .output(outputPattern)
      .outputOptions([
        '-f segment',
        `-segment_time ${chunkDuration}`,
        '-c copy',
        '-reset_timestamps 1'
      ])
      .on('end', resolve)
      .on('error', reject)
      .run();
  });
};

// Extract audio from video and split
const extractAudioAndSplit = async (videoBuffer, maxChunkSizeBytes, originalFileName) => {
  const tempDir = path.join(os.tmpdir(), uuidv4());

  try {
    // Create temp directory
    fs.mkdirSync(tempDir, { recursive: true });

    const baseFileName = path.basename(originalFileName);
    const inputFile = path.join(tempDir, baseFileName);
    const fileNameWithoutExt = path.parse(baseFileName).name;
    const outputMp3 = path.join(tempDir, `${fileNameWithoutExt}.mp3`);

    // Write video buffer to file
    fs.writeFileSync(inputFile, videoBuffer);

    // Extract audio from video
    await new Promise((resolve, reject) => {
      ffmpeg(inputFile)
        .output(outputMp3)
        .audioCodec('libmp3lame')
        .audioBitrate(192)
        .noVideo()
        .on('end', resolve)
        .on('error', reject)
        .run();
    });

    // Read the MP3 file
    const mp3Buffer = fs.readFileSync(outputMp3);

    // Split the audio file
    const chunks = await splitAudioFile(
      mp3Buffer,
      maxChunkSizeBytes,
      `${fileNameWithoutExt}.mp3`
    );

    return chunks;
  } catch (error) {
    console.error('Error extracting audio and splitting:', error);
    throw error;
  } finally {
    // Clean up temporary files
    try {
      fs.rmSync(tempDir, { recursive: true, force: true });
    } catch (error) {
      console.error('Error cleaning up temporary files:', error);
    }
  }
};

// Transcribe audio chunks
const transcribeChunks = async (chunks) => {
  const transcribedResults = [];

  for (let i = 0; i < chunks.length; i++) {
    const chunk = chunks[i];
    console.log(`Starting transcription for chunk ${i}: ${chunk.file_name}`);

    try {
      // Write chunk to temporary file
      const tempDir = path.join(os.tmpdir(), 'transcribe');
      fs.mkdirSync(tempDir, { recursive: true });
      const tempFilePath = path.join(tempDir, chunk.file_name);
      fs.writeFileSync(tempFilePath, chunk.data);

      // Transcribe using OpenAI
      const transcription = await openai.audio.transcriptions.create({
        file: fs.createReadStream(tempFilePath),
        model: config.OPENAI_MODEL,
      });

      console.log(`Transcription completed for chunk ${i}`);

      // Clean up
      fs.unlinkSync(tempFilePath);

      transcribedResults.push(transcription.text);
    } catch (error) {
      console.error(`Error transcribing chunk ${i}:`, error);
      throw error;
    }
  }

  return transcribedResults;
};

module.exports = {
  splitAudioFile,
  extractAudioAndSplit,
  transcribeChunks
};
