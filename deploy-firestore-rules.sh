#!/bin/bash

# Deploy Firestore Security Rules to Firebase

echo "🔥 Deploying Firestore Security Rules..."

# Check if Firebase CLI is installed
if ! command -v firebase &> /dev/null; then
    echo "❌ Firebase CLI not found. Installing..."
    npm install -g firebase-tools
fi

# Login to Firebase (if needed)
echo "🔑 Checking Firebase authentication..."
firebase projects:list > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "🔑 Please login to Firebase..."
    firebase login
fi

# Set the project
echo "🎯 Setting Firebase project to hackathon-462905..."
firebase use hackathon-462905

# Deploy Firestore rules
echo "📋 Deploying Firestore security rules..."
firebase deploy --only firestore:rules

echo "✅ Firestore rules deployed successfully!"
echo ""
echo "🔗 You can view the rules in Firebase Console:"
echo "   https://console.firebase.google.com/project/hackathon-462905/firestore/rules"