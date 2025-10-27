import '../styles/LoadingSpinner.css'

const LoadingSpinner = () => {
  return (
    <div className="loading-container">
      <div className="spinner"></div>
      <p>Carregando dados da F1...</p>
    </div>
  )
}

export default LoadingSpinner
