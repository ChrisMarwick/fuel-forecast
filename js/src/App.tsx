import './App.css'

function App() {

  return (
    <div className="flex">
      <div className="border-2 rounded-md p-4 bg-blue-300 mr-4">
        <h1 className="text-center">$138.60</h1>
        <h3>
          Hello world!
        </h3>
      </div>
      <div className="border-2 rounded-md p-4 bg-red-300 mr-4 opacity-90">
        <h1 className="text-center">$150.60</h1>
        <h3>
          Hello world!
        </h3>
      </div>
      <div className="border-2 rounded-md p-4 bg-red-300 opacity-75">
        <h1 className="text-center">$170.60</h1>
        <h3>
          Hello world!
        </h3>
      </div>
    </div>
  )
}

export default App
