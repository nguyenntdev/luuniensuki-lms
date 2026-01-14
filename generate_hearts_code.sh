#!/bin/bash

# Navigate to mobile directory
cd mobile

# Run build_runner to generate freezed and riverpod code
echo "Generating code with build_runner..."
flutter pub run build_runner build --delete-conflicting-outputs

echo "Code generation complete!"

