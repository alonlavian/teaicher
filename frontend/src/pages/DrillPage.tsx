import {
  Box,
  VStack,
  Text,
  Button,
  useToast,
  Textarea,
  Heading,
  Card,
  CardBody,
  Spinner,
  Alert,
  AlertIcon,
  Input,
  HStack,
  Divider,
} from '@chakra-ui/react'
import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import axios from 'axios'

interface DrillData {
  question: string
  answer: string
  hint: string
}

function DrillPage() {
  const { subject } = useParams<{ subject: string }>()
  const [userAnswer, setUserAnswer] = useState('')
  const [chatMessage, setChatMessage] = useState('')
  const [chatHistory, setChatHistory] = useState<Array<{ role: 'user' | 'assistant', content: string }>>([])
  const toast = useToast()

  const { data: drill, isLoading } = useQuery<DrillData>({
    queryKey: ['drill', subject],
    queryFn: async () => {
      const response = await axios.post('/api/get_drill', { subject })
      return response.data
    },
  })

  const checkAnswer = useMutation({
    mutationFn: async (answer: string) => {
      const response = await axios.post('/api/check_answer', { answer })
      return response.data
    },
    onSuccess: (data) => {
      toast({
        title: data.correct ? 'Correct!' : 'Try Again',
        description: data.feedback,
        status: data.correct ? 'success' : 'info',
        duration: 5000,
      })
      if (data.correct) {
        setUserAnswer('')
        // Refetch the drill
        window.location.reload()
      }
    },
  })

  const sendMessage = useMutation({
    mutationFn: async (message: string) => {
      const response = await axios.post('/api/chat', { message })
      return response.data
    },
    onSuccess: (data) => {
      setChatHistory(prev => [
        ...prev,
        { role: 'assistant', content: data.response }
      ])
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.error || 'Failed to send message',
        status: 'error',
        duration: 5000,
      })
    }
  })

  const handleSubmit = () => {
    if (!userAnswer.trim()) {
      toast({
        title: 'Please enter an answer',
        status: 'warning',
        duration: 3000,
      })
      return
    }
    checkAnswer.mutate(userAnswer)
  }

  const handleSendMessage = () => {
    if (!chatMessage.trim()) return
    
    setChatHistory(prev => [
      ...prev,
      { role: 'user', content: chatMessage }
    ])
    sendMessage.mutate(chatMessage)
    setChatMessage('')
  }

  if (isLoading) {
    return (
      <Box textAlign="center" py={20}>
        <Spinner size="xl" />
        <Text mt={4}>Loading drill...</Text>
      </Box>
    )
  }

  if (!drill) {
    return (
      <Alert status="error">
        <AlertIcon />
        Failed to load drill. Please try again.
      </Alert>
    )
  }

  return (
    <VStack spacing={8} align="stretch" p={4} maxW="container.lg" mx="auto">
      <Box textAlign="center">
        <Heading size="xl" mb={4}>
          {subject?.charAt(0).toUpperCase() + subject?.slice(1)} Practice
        </Heading>
      </Box>

      <Card>
        <CardBody>
          <VStack spacing={6}>
            <Text fontSize="xl" fontWeight="medium">
              {drill.question}
            </Text>

            <Textarea
              value={userAnswer}
              onChange={(e) => setUserAnswer(e.target.value)}
              placeholder="Enter your answer here..."
              size="lg"
              rows={4}
            />

            <Button
              colorScheme="blue"
              size="lg"
              onClick={handleSubmit}
              isLoading={checkAnswer.isPending}
              w="full"
            >
              Submit Answer
            </Button>
          </VStack>
        </CardBody>
      </Card>

      <Divider />

      <Card>
        <CardBody>
          <VStack spacing={4} align="stretch">
            <Heading size="md">Need Help?</Heading>
            
            <Box maxH="300px" overflowY="auto">
              {chatHistory.map((msg, idx) => (
                <Box
                  key={idx}
                  bg={msg.role === 'user' ? 'blue.50' : 'gray.50'}
                  p={3}
                  borderRadius="md"
                  mb={2}
                >
                  <Text>{msg.content}</Text>
                </Box>
              ))}
            </Box>

            <HStack>
              <Input
                value={chatMessage}
                onChange={(e) => setChatMessage(e.target.value)}
                placeholder="Ask for help..."
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              />
              <Button
                colorScheme="blue"
                onClick={handleSendMessage}
                isLoading={sendMessage.isPending}
              >
                Send
              </Button>
            </HStack>
          </VStack>
        </CardBody>
      </Card>
    </VStack>
  )
}

export default DrillPage
