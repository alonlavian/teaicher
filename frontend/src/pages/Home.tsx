import {
  SimpleGrid,
  Box,
  Heading,
  Text,
  Icon,
  VStack,
  useColorModeValue,
} from '@chakra-ui/react'
import { useNavigate } from 'react-router-dom'
import {
  FaSquareRootAlt,
  FaShapes,
  FaCalculator,
  FaChartBar,
} from 'react-icons/fa'

const subjects = [
  {
    id: 'algebra',
    name: 'Algebra',
    description: 'Learn equations, functions, and mathematical patterns',
    icon: FaSquareRootAlt,
  },
  {
    id: 'geometry',
    name: 'Geometry',
    description: 'Study shapes, sizes, and positions of figures',
    icon: FaShapes,
  },
  {
    id: 'arithmetic',
    name: 'Arithmetic',
    description: 'Master basic mathematical operations',
    icon: FaCalculator,
  },
  {
    id: 'statistics',
    name: 'Statistics',
    description: 'Understand data analysis and probability',
    icon: FaChartBar,
  },
]

function Home() {
  const navigate = useNavigate()
  const bgColor = useColorModeValue('white', 'gray.700')
  const hoverBgColor = useColorModeValue('gray.50', 'gray.600')

  return (
    <VStack spacing={8} align="stretch">
      <Box textAlign="center">
        <Heading size="2xl" mb={4}>
          Choose a Subject
        </Heading>
        <Text fontSize="lg" color="gray.500">
          Select a subject to start practicing
        </Text>
      </Box>

      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={6}>
        {subjects.map((subject) => (
          <Box
            key={subject.id}
            bg={bgColor}
            p={6}
            rounded="xl"
            shadow="md"
            cursor="pointer"
            onClick={() => navigate(`/drill/${subject.id}`)}
            transition="all 0.2s"
            _hover={{
              transform: 'translateY(-4px)',
              shadow: 'lg',
              bg: hoverBgColor,
            }}
          >
            <VStack spacing={4} align="center">
              <Icon as={subject.icon} boxSize={12} color="blue.500" />
              <Heading size="md">{subject.name}</Heading>
              <Text color="gray.500" textAlign="center">
                {subject.description}
              </Text>
            </VStack>
          </Box>
        ))}
      </SimpleGrid>
    </VStack>
  )
}

export default Home
