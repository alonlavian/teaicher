import { useQuery, useMutation } from '@tanstack/react-query'
import axios from 'axios'

interface User {
  id: string
  username: string
  email: string
  total_score: number
  created_at: string
  preferred_language: string
}

interface LoginData {
  username: string
  password: string
}

interface RegisterData extends LoginData {
  email: string
  confirm_password: string
}

export function useAuth() {
  const { data: user, isLoading, refetch } = useQuery<User>({
    queryKey: ['user'],
    queryFn: async () => {
      try {
        const response = await axios.get('/api/profile')
        return response.data
      } catch (error) {
        return null
      }
    },
  })

  const login = useMutation({
    mutationFn: async (data: LoginData) => {
      const response = await axios.post('/api/login', data)
      return response.data
    },
    onSuccess: () => {
      refetch()
    },
  })

  const register = useMutation({
    mutationFn: async (data: RegisterData) => {
      const response = await axios.post('/api/register', data)
      return response.data
    },
  })

  const logout = useMutation({
    mutationFn: async () => {
      const response = await axios.get('/api/logout')
      return response.data
    },
    onSuccess: () => {
      refetch()
    },
  })

  return {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
  }
}
