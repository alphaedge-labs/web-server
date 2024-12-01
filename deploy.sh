#!/bin/bash

echo "🚀 Starting the build process..."
docker compose build
if [ $? -eq 0 ]; then
  echo "✅ Build completed successfully!"
else
  echo "❌ Build failed. Please check the errors above. 💔"
  exit 1
fi

echo "🛑 Shutting down any running containers..."
docker compose down
if [ $? -eq 0 ]; then
  echo "✅ Containers stopped successfully! 🧹"
else
  echo "❌ Failed to stop containers. Please check for issues. 😢"
  exit 1
fi

echo "🔧 Starting up containers in detached mode..."
docker compose up -d
if [ $? -eq 0 ]; then
  echo "🎉 Containers are up and running! 🌟"
  echo "🌐 Visit your application to check if everything is working as expected!"
else
  echo "❌ Failed to start containers. Please troubleshoot. 🛠️"
  exit 1
fi

echo "✨ Deployment completed successfully! 🎉 Have a great day! 😊"