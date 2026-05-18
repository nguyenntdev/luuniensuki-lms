#!/usr/bin/env node

/**
 * Model Compression Script
 * 
 * Compresses GLB models using gltf-pipeline with Draco compression
 * for optimal mobile performance and reduced bandwidth usage.
 */

const gltfPipeline = require('gltf-pipeline');
const fsExtra = require('fs-extra');
const path = require('path');
const { performance } = require('perf_hooks');

// Configuration
const CONFIG = {
  dracoOptions: {
    compressionLevel: 7, // 0-10, higher = better compression but slower
    quantizePositionBits: 14,
    quantizeNormalBits: 10,
    quantizeTexcoordBits: 12,
    quantizeColorBits: 8,
    quantizeGenericBits: 12,
    unifiedQuantization: false
  },
  compressDracoMeshes: true,
  outputSuffix: '.compressed',
  inputDir: process.argv[2] || path.join(__dirname, '..', 'assets', 'models'),
  outputDir: process.argv[3] || null, // If null, output to same directory as input
  skipExisting: false
};

// Statistics tracking
const stats = {
  totalFiles: 0,
  processedFiles: 0,
  failedFiles: 0,
  skippedFiles: 0,
  totalOriginalSize: 0,
  totalCompressedSize: 0,
  startTime: 0,
  errors: []
};

/**
 * Format bytes to human-readable string
 */
function formatBytes(bytes, decimals = 2) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

/**
 * Calculate compression ratio
 */
function getCompressionRatio(original, compressed) {
  return ((1 - compressed / original) * 100).toFixed(2);
}

/**
 * Get all GLB files in directory
 */
async function getGLBFiles(dir) {
  const files = await fsExtra.readdir(dir);
  return files
    .filter(file => file.toLowerCase().endsWith('.glb') && !file.includes('.compressed'))
    .map(file => path.join(dir, file));
}

/**
 * Compress a single GLB file
 */
async function compressModel(inputPath) {
  const fileName = path.basename(inputPath);
  const fileDir = path.dirname(inputPath);
  const fileExt = path.extname(inputPath);
  const fileBase = path.basename(inputPath, fileExt);
  
  const outputDir = CONFIG.outputDir || fileDir;
  const outputPath = path.join(outputDir, `${fileBase}${CONFIG.outputSuffix}${fileExt}`);
  
  console.log(`\n📦 Processing: ${fileName}`);
  
  // Check if output already exists
  if (CONFIG.skipExisting && await fsExtra.pathExists(outputPath)) {
    console.log(`⏭️  Skipped (already exists): ${path.basename(outputPath)}`);
    stats.skippedFiles++;
    return null;
  }
  
  try {
    // Read input file
    const inputBuffer = await fsExtra.readFile(inputPath);
    const originalSize = inputBuffer.length;
    
    console.log(`   Original size: ${formatBytes(originalSize)}`);
    
    // Compress with gltf-pipeline
    const startTime = performance.now();
    
    const result = await gltfPipeline.processGlb(inputBuffer, {
      dracoOptions: CONFIG.dracoOptions,
      separate: false, // Keep as GLB (not separate gltf + bin)
      separateTextures: false,
      stats: false
    });
    
    const endTime = performance.now();
    const compressionTime = ((endTime - startTime) / 1000).toFixed(2);
    
    // Ensure output directory exists
    await fsExtra.ensureDir(outputDir);
    
    // Write compressed file
    await fsExtra.writeFile(outputPath, result.glb);
    const compressedSize = result.glb.length;
    
    const ratio = getCompressionRatio(originalSize, compressedSize);
    const saved = originalSize - compressedSize;
    
    console.log(`   Compressed size: ${formatBytes(compressedSize)}`);
    console.log(`   Size reduction: ${formatBytes(saved)} (${ratio}%)`);
    console.log(`   Time taken: ${compressionTime}s`);
    console.log(`   ✅ Saved to: ${path.basename(outputPath)}`);
    
    stats.processedFiles++;
    stats.totalOriginalSize += originalSize;
    stats.totalCompressedSize += compressedSize;
    
    return {
      inputPath,
      outputPath,
      originalSize,
      compressedSize,
      ratio: parseFloat(ratio),
      compressionTime: parseFloat(compressionTime)
    };
    
  } catch (error) {
    console.error(`   ❌ Error: ${error.message}`);
    stats.failedFiles++;
    stats.errors.push({ file: fileName, error: error.message });
    return null;
  }
}

/**
 * Main execution
 */
async function main() {
  console.log('🚀 GLB Model Compression Tool');
  console.log('================================\n');
  
  stats.startTime = performance.now();
  
  // Verify input directory exists
  if (!await fsExtra.pathExists(CONFIG.inputDir)) {
    console.error(`❌ Input directory does not exist: ${CONFIG.inputDir}`);
    process.exit(1);
  }
  
  console.log(`📁 Input directory: ${CONFIG.inputDir}`);
  console.log(`📁 Output directory: ${CONFIG.outputDir || 'Same as input'}`);
  console.log(`⚙️  Draco compression level: ${CONFIG.dracoOptions.compressionLevel}\n`);
  
  // Get all GLB files
  const glbFiles = await getGLBFiles(CONFIG.inputDir);
  stats.totalFiles = glbFiles.length;
  
  if (glbFiles.length === 0) {
    console.log('⚠️  No GLB files found in the input directory.');
    process.exit(0);
  }
  
  console.log(`Found ${glbFiles.length} GLB file(s) to compress.\n`);
  
  // Process each file
  const results = [];
  for (const filePath of glbFiles) {
    const result = await compressModel(filePath);
    if (result) {
      results.push(result);
    }
  }
  
  // Print summary
  const endTime = performance.now();
  const totalTime = ((endTime - stats.startTime) / 1000).toFixed(2);
  
  console.log('\n' + '='.repeat(50));
  console.log('📊 COMPRESSION SUMMARY');
  console.log('='.repeat(50));
  console.log(`Total files found:     ${stats.totalFiles}`);
  console.log(`Successfully processed: ${stats.processedFiles}`);
  console.log(`Failed:                ${stats.failedFiles}`);
  console.log(`Skipped:               ${stats.skippedFiles}`);
  console.log(`Total time:            ${totalTime}s`);
  
  if (stats.processedFiles > 0) {
    const totalRatio = getCompressionRatio(stats.totalOriginalSize, stats.totalCompressedSize);
    const totalSaved = stats.totalOriginalSize - stats.totalCompressedSize;
    
    console.log('\n💾 Storage Statistics:');
    console.log(`Original total size:   ${formatBytes(stats.totalOriginalSize)}`);
    console.log(`Compressed total size: ${formatBytes(stats.totalCompressedSize)}`);
    console.log(`Total space saved:     ${formatBytes(totalSaved)} (${totalRatio}%)`);
  }
  
  if (stats.errors.length > 0) {
    console.log('\n❌ Errors:');
    stats.errors.forEach(({ file, error }) => {
      console.log(`   - ${file}: ${error}`);
    });
  }
  
  console.log('\n✨ Compression complete!\n');
  
  // Exit with error code if any files failed
  process.exit(stats.failedFiles > 0 ? 1 : 0);
}

// Run if executed directly
if (require.main === module) {
  main().catch(error => {
    console.error('\n❌ Fatal error:', error);
    process.exit(1);
  });
}

module.exports = { compressModel, getGLBFiles, CONFIG };

