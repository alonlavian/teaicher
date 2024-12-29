import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Input,
  VStack,
  Text,
  useToast,
  Container,
  Heading,
  Link,
} from '@chakra-ui/react'
import { useState } from 'react'
import { Link as RouterLink } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const { login } = useAuth()
  const toast = useToast()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await login.mutateAsync({ username, password })
      toast({
        title: 'Login successful',
        status: 'success',
        duration: 3000,
      })
    } catch (error: any) {
      toast({
        title: 'Login failed',
        description: error.response?.data?.error || 'Something went wrong',
        status: 'error',
        duration: 3000,
      })
    }
  }

  return (
    <Container maxW="container.sm" py={20}>
      <Box
        p={8}
        bg="white"
        _dark={{ bg: 'gray.700' }}
        rounded="xl"
        shadow="lg"
      >
        <VStack spacing={6}>
          <Heading>Welcome Back</Heading>
          <Text color="gray.500">Sign in to continue learning</Text>

          <form onSubmit={handleSubmit} style={{ width: '100%' }}>
            <VStack spacing={4} w="100%">
              <FormControl isRequired>
                <FormLabel>Username</FormLabel>
                <Input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                />
              </FormControl>

              <FormControl isRequired>
                <FormLabel>Password</FormLabel>
                <Input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </FormControl>

              <Button
                type="submit"
                colorScheme="blue"
                size="lg"
                w="100%"
                isLoading={login.isPending}
              >
                Sign In
              </Button>
            </VStack>
          </form>

          <Text>
            Don't have an account?{' '}
            <Link as={RouterLink} to="/register" color="blue.500">
              Register now
            </Link>
          </Text>
        </VStack>
      </Box>
    </Container>
  )
}

export default Login
