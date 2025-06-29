#!/bin/bash

echo "🧪 Starting Expert Company LLM Assistant Automated Test"
echo "=================================================="

# Set test environment
export OPENAI_API_KEY="test-key"
export DATABASE_URL="sqlite:///test.db"
export ENVIRONMENT="test"

cd backend

echo "📋 Step 1: Testing imports and basic functionality..."
python3 simple_test.py
if [ $? -eq 0 ]; then
    echo "✅ Basic tests passed"
else
    echo "❌ Basic tests failed"
    exit 1
fi

echo "📋 Step 2: Testing data integrity..."
python3 test_task2.py
if [ $? -eq 0 ]; then
    echo "✅ Data integrity tests passed"
else
    echo "❌ Data integrity tests failed"
    exit 1
fi

echo "📋 Step 3: Testing multilingual features..."
python3 test_task4_task5.py
if [ $? -eq 0 ]; then
    echo "✅ Multilingual tests passed"
else
    echo "❌ Multilingual tests failed"
    exit 1
fi

echo "🎉 All automated tests completed successfully!"
echo "🚀 System is ready for production deployment!" 