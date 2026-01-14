#!/usr/bin/env node

/**
 * Test Compression Script
 * 
 * This script downloads a sample GLB model and tests the compression
 * to demonstrate the compression capabilities and verify the setup.
 */

const https = require('https');
const fs = require('fs');
const path = require('path');

const TEST_MODEL_URL = 'https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/Box/glTF-Binary/Box.glb';
const TEST_MODEL_NAME = 'test-model.glb';
const TEST_DIR = path.join(__dirname, 'test-output');

console.log('🧪 Model Compression Test\n');

// Create test directory
if (!fs.existsSync(TEST_DIR)) {
  fs.mkdirSync(TEST_DIR, { recursive: true });
}

const testModelPath = path.join(TEST_DIR, TEST_MODEL_NAME);

// Download test model
console.log('📥 Downloading test model...');
console.log(`   URL: ${TEST_MODEL_URL}`);

const file = fs.createWriteStream(testModelPath);

https.get(TEST_MODEL_URL, (response) => {
  response.pipe(file);
  
  file.on('finish', () => {
    file.close();
    console.log(`   ✅ Downloaded to: ${testModelPath}\n`);
    
    // Run compression test
    console.log('🚀 Running compression test...\n');
    
    const { spawn } = require('child_process');
    const compressProcess = spawn('node', [
      path.join(__dirname, 'compress-models.js'),
      TEST_DIR
    ], {
      stdio: 'inherit'
    });
    
    compressProcess.on('close', (code) => {
      if (code === 0) {
        console.log('\n✨ Test completed successfully!');
        console.log(`\nTest files are located at: ${TEST_DIR}`);
        console.log('You can safely delete this directory when done.\n');
      } else {
        console.log('\n❌ Test failed. Please check the error messages above.\n');
        process.exit(1);
      }
    });
  });
}).on('error', (err) => {
  fs.unlink(testModelPath, () => {});
  console.error(`\n❌ Download failed: ${err.message}\n`);
  process.exit(1);
});

